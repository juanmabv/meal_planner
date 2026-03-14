import json
from pathlib import Path
from typing import Dict, List, Literal
from random import choice
from models.meal_plan import MealPlan, MealDay
from models.recipe import Recipe, MealType
from services.inventory_service import InventoryService
from services.recipe_service import RecipeService
from services.unit_conversion_service import UnitConversionService

OptimizationGoal = Literal["minimize_shopping", "minimize_prep_time", "use_expiring_food"]

class MealPlannerService:
    """
    Service for planning meals.

    Generates a meal plan based on days, inventory, recipes, and optimization goals.
    """

    def __init__(self, inventory_service: InventoryService, recipe_service: RecipeService):
        self.inventory_service = inventory_service
        self.recipe_service = recipe_service
        self.products_file = Path("data/products.json")
        self._products: Dict[str, str] = {}  # name to barcode
        self._load_products()

    def _load_products(self):
        """Loads products to map names to barcodes."""
        with open(self.products_file, 'r') as f:
            data = json.load(f)
        for p in data:
            self._products[p['name']] = p['barcode']

    def plan_meals(
        self,
        days_to_cover: int,
        allow_same_meal_same_day: bool = False,
        allow_recipe_repetition: bool = True,
        optimization_goal: OptimizationGoal = "minimize_shopping"
    ) -> MealPlan:
        """
        Plans meals for the given number of days.

        Args:
            days_to_cover (int): Number of days to plan.
            allow_same_meal_same_day (bool): Allow same recipe for different meals in a day.
            allow_recipe_repetition (bool): Allow repeating recipes across days.
            optimization_goal (OptimizationGoal): Goal for optimization.

        Returns:
            MealPlan: The planned meals.
        """
        recipes = self.recipe_service.get_all_recipes()
        available_inventory = self.inventory_service.get_available_inventory()

        # Group recipes by meal type
        recipes_by_type: Dict[MealType, List[Recipe]] = {
            "breakfast": [],
            "lunch": [],
            "dinner": []
        }
        for recipe in recipes:
            recipes_by_type[recipe.meal_type].append(recipe)

        meal_plan: MealPlan = {}
        used_recipes = set() if not allow_recipe_repetition else None

        for day in range(1, days_to_cover + 1):
            day_recipes = set() if not allow_same_meal_same_day else None
            meals = {}
            for meal_type in ["breakfast", "lunch", "dinner"]:
                candidates = recipes_by_type[meal_type]
                if not allow_recipe_repetition and used_recipes is not None:
                    candidates = [r for r in candidates if r.name not in used_recipes]
                if not allow_same_meal_same_day and day_recipes is not None:
                    candidates = [r for r in candidates if r.name not in day_recipes]

                if not candidates:
                    # Fallback, perhaps repeat or choose any
                    candidates = recipes_by_type[meal_type]

                # Select based on optimization
                selected = self._select_recipe(candidates, available_inventory, optimization_goal)
                meals[meal_type] = selected.name

                if not allow_recipe_repetition and used_recipes is not None:
                    used_recipes.add(selected.name)
                if not allow_same_meal_same_day and day_recipes is not None:
                    day_recipes.add(selected.name)

            meal_plan[day] = MealDay(**meals)

        return meal_plan

    def _select_recipe(self, candidates: List[Recipe], inventory: Dict[str, float], goal: OptimizationGoal) -> Recipe:
        """
        Selects a recipe from candidates based on the optimization goal.

        For simplicity, selects the one that uses the most inventory.
        """
        if goal == "minimize_shopping":
            # Prefer recipes that use more available inventory
            def score(recipe: Recipe) -> float:
                total_used = 0.0
                for ing in recipe.ingredients:
                    barcode = self._products.get(ing.ingredient_name)  # Map name to barcode
                    if barcode and barcode in inventory:
                        req_norm, _ = UnitConversionService.normalize_quantity(ing.quantity, ing.unit)
                        available = inventory[barcode]
                        total_used += min(req_norm, available)
                return total_used
            candidates.sort(key=score, reverse=True)
            return candidates[0] if candidates else choice(candidates)
        else:
            # For other goals, random for now
            return choice(candidates) if candidates else None  # But assume always have
