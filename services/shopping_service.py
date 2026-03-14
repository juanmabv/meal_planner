import json
from typing import Dict, List, Tuple
from pathlib import Path
from collections import defaultdict

from models.shopping_list import ShoppingList, ShoppingListItem
from models.meal_plan import MealPlan
from models.food_item import FoodItem
from services.recipe_service import RecipeService
from services.inventory_service import InventoryService
from services.unit_conversion_service import UnitConversionService

class ShoppingService:
    """
    Service for generating shopping lists.

    Calculates missing ingredients and selects appropriate products.
    """

    def __init__(self, recipe_service: RecipeService, inventory_service: InventoryService, products_file: str = "data/products.json"):
        self.recipe_service = recipe_service
        self.inventory_service = inventory_service
        self.products_file = Path(products_file)
        self._products: Dict[str, List[FoodItem]] = {}
        self._load_products()

    def _load_products(self):
        """Loads products from JSON."""
        with open(self.products_file, 'r') as f:
            data = json.load(f)
        for product_data in data:
            product = FoodItem(
                barcode=product_data['barcode'],
                name=product_data['name'],
                category=product_data['category'],
                unit_type=product_data['unit_type'],
                package_quantity=product_data['package_quantity'],
                package_unit=product_data['package_unit'],
                serving_size=product_data['serving_size'],
                serving_unit=product_data['serving_unit'],
                price=product_data.get('price')
            )
            if product.name not in self._products:
                self._products[product.name] = []
            self._products[product.name].append(product)

    def calculate_missing_ingredients(self, meal_plan: MealPlan) -> Dict[str, Tuple[float, str]]:
        """
        Calculates total ingredient requirements from meal plan and subtracts available inventory.

        Returns:
            Dict[str, Tuple[float, str]]: Ingredient name to (missing_quantity, unit).
        """
        total_required: Dict[str, Tuple[float, str]] = defaultdict(lambda: (0.0, ""))
        available = self.inventory_service.get_available_inventory()

        # But available is by barcode, need by name.
        # Problem again.
        # Need to map barcode to name.
        # Since products have name and barcode, can make a dict barcode to name.
        barcode_to_name = {}
        for products in self._products.values():
            for p in products:
                barcode_to_name[p.barcode] = p.name

        available_by_name = {}
        for barcode, qty in available.items():
            name = barcode_to_name.get(barcode)
            if name:
                if name in available_by_name:
                    available_by_name[name] += qty  # Assume same unit type
                else:
                    available_by_name[name] = qty

        # Now, for each meal in plan
        for day, meal_day in meal_plan.items():
            for meal_type, recipe_name in [("breakfast", meal_day.breakfast), ("lunch", meal_day.lunch), ("dinner", meal_day.dinner)]:
                req = self.recipe_service.calculate_ingredient_requirements(recipe_name, 1)  # Assume 1 serving per meal
                for ing_name, (qty, unit) in req.items():
                    norm_req, norm_unit = UnitConversionService.normalize_quantity(qty, unit)
                    if ing_name in total_required:
                        existing_norm, _ = UnitConversionService.normalize_quantity(total_required[ing_name][0], total_required[ing_name][1])
                        total_required[ing_name] = (existing_norm + norm_req, norm_unit)
                    else:
                        total_required[ing_name] = (norm_req, norm_unit)

        # Now subtract available
        missing = {}
        for ing_name, (req_norm, norm_unit) in total_required.items():
            avail_norm = available_by_name.get(ing_name, 0.0)
            miss_norm = max(0, req_norm - avail_norm)
            if miss_norm > 0:
                missing[ing_name] = (miss_norm, norm_unit)

        return missing

    def generate_shopping_list(self, missing: Dict[str, Tuple[float, str]]) -> ShoppingList:
        """
        Generates shopping list from missing ingredients.

        Args:
            missing (Dict[str, Tuple[float, str]]): Missing ingredients.

        Returns:
            ShoppingList: List of items to buy.
        """
        shopping_list = []
        for ing_name, (miss_qty, miss_unit) in missing.items():
            products = self._products.get(ing_name, [])
            if not products:
                continue  # No product found
            # Choose the smallest package that satisfies
            # Convert miss_qty to package units
            suitable = []
            for p in products:
                # Convert package_quantity to normalized
                pack_norm, _ = UnitConversionService.normalize_quantity(p.package_quantity, p.package_unit)
                if pack_norm >= miss_qty:
                    suitable.append(p)
            if suitable:
                # Choose smallest
                suitable.sort(key=lambda p: UnitConversionService.normalize_quantity(p.package_quantity, p.package_unit)[0])
                chosen = suitable[0]
                # quantity_to_buy is the package quantity, but spec says quantity_to_buy, and in partial, it's the missing.
                # Wait, spec: "If recipe requires 100g sugar and inventory has 50g sugar Shopping list should contain 50g sugar"
                # So, quantity_to_buy = miss_qty, unit = miss_unit
                # But then, how to choose package? The package is chosen, but quantity_to_buy is the amount needed, not the package size.
                # But in model, quantity_to_buy, and for output, product_name - quantity - unit
                # So, probably quantity_to_buy = miss_qty, unit = miss_unit, but to choose product, the one with smallest package >= miss_qty
                # But if miss_qty = 50g, and packages 1kg, 150g, choose 150g, but quantity_to_buy = 50g, unit = g
                # But the output is product_name - 50g - g
                # But the product is 150g package.
                # But the model has product_barcode, so can buy the 150g package for 50g needed.
                # But the spec says "choose the smallest package that satisfies the requirement"
                # So, quantity_to_buy = package_quantity, unit = package_unit
                # But in partial, for 50g, buy 150g package, quantity_to_buy = 150, unit = g
                # But the output is product_name - 150 - g
                # But the spec says "Shopping list should contain 50g sugar"
                # Contradiction.
                # Looking back: "If required quantity = 50g choose the smallest package that satisfies the requirement."
                # So, buy the 150g package, but the quantity in list is 150g.
                # But in partial rule, "Shopping list should contain 50g sugar" but that seems for the amount to buy, but then choose package.
                # Perhaps quantity_to_buy is the amount needed, and product is chosen accordingly.
                # But to match, perhaps quantity_to_buy = miss_qty, unit = miss_unit
                # And choose product with smallest package >= miss_qty
                # Yes, and the output is product_name - quantity - unit, where quantity is miss_qty.
                # And the barcode is of the chosen product.
                # Yes, that makes sense.
                # For example, buy "sugar 150g" for 50g needed.
                # But the list says sugar - 50 - g
                # Yes.
                # And estimated_price = price of the package.
                # But if price is per package, and buying the package, but since quantity is not the package, perhaps price * (miss_qty / package_qty)
                # But spec has estimated_price, probably for the quantity.
                # But since price is per package, need to calculate.
                # For simplicity, if price, estimated_price = price * (miss_qty / package_qty)
                # But if miss_qty > package_qty, but since chosen >=, but if miss_qty > package_qty, perhaps buy multiple, but for simplicity, assume one package.
                # But spec doesn't say multiple packages.
                # For now, assume buy one package, quantity_to_buy = package_quantity, unit = package_unit, estimated_price = price
                # But that contradicts the partial rule example.
                # The partial rule says "Shopping list should contain 50g sugar" meaning the amount to buy is 50g, but since packages are larger, perhaps it's the amount, and buy the package that covers it.
                # I think quantity_to_buy is the amount needed, unit is the normalized or original.
                # And the product is chosen.
                # Yes, and for output, it's the amount.
                # And barcode of the product.
                # For price, if price, estimated_price = price * (miss_qty / package_qty)
                # But since package_qty is in package_unit, need to convert.
                # To simplify, assume unit is g for weight, etc.
                # For now, let's set quantity_to_buy = miss_qty, unit = miss_unit, estimated_price = chosen.price if chosen.price else 0.0
                # But if price is per package, and miss_qty < package_qty, price should be proportional.
                # Yes, let's do that.
                pack_norm, _ = UnitConversionService.normalize_quantity(chosen.package_quantity, chosen.package_unit)
                proportion = miss_qty / pack_norm
                est_price = chosen.price * proportion if chosen.price else 0.0
                item = ShoppingListItem(
                    product_barcode=chosen.barcode,
                    product_name=chosen.name,
                    quantity_to_buy=miss_qty,
                    unit=miss_unit,
                    estimated_price=est_price
                )
                shopping_list.append(item)

        return shopping_list
