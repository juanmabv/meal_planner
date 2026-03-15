"""
Create a Python 3.10 CLI application that implements a meal planning and grocery optimization system.

GOAL
The system generates:
1. A meal plan
2. A shopping list

based on:
- the number of days to cover
- 3 meals per day
- the current food inventory
- a recipe database
- a food product database with package sizes

The system should maximize the use of available food and generate a shopping list only for missing ingredients.


PROJECT STRUCTURE

meal_planner/

    main.py

    models/
        food_item.py
        inventory_item.py
        recipe.py
        recipe_ingredient.py
        shopping_list.py
        meal_plan.py

    services/
        inventory_service.py
        recipe_service.py
        meal_planner_service.py
        shopping_service.py
        unit_conversion_service.py

    cli/
        cli_parser.py

    data/
        recipes.json
        products.json
        inventory.json

    outputs/
        shopping_lists/


GENERAL RULES

Python version: 3.10
Use:
- dataclasses
- type hints
- modular architecture
- docstrings

All data is stored locally in JSON files.


UNIT SYSTEM

The system must normalize units to the International System.

Weight → kilograms
Volume → liters

Allowed unit types:

weight
volume
count

Examples:
grams → kilograms
milliliters → liters

Create a UnitConversionService that handles these conversions.


SERVING SYSTEM

All calculations should ultimately work in terms of "servings".

Each product has:

serving_size
serving_unit

Example:

water bottle:
quantity: 2 liters
serving_size: 0.25 liters

This means the bottle contains 8 servings.

Recipes also define ingredient quantities that correspond to a specific number of servings.


FOOD PRODUCT MODEL

Food products represent purchasable items.

Fields:

barcode: str
name: str
category: str
unit_type: weight | volume | count
package_quantity: float
package_unit: str
serving_size: float
serving_unit: str
price: float | None

Multiple products may exist for the same ingredient but with different package sizes.


INVENTORY ITEM MODEL

Represents a specific item owned by the user.

Fields:

barcode: str
quantity: float
unit: str
purchase_date: datetime
opened_date: datetime | None
expiration_date: datetime
storage_location: pantry | fridge | freezer

Expired items must be ignored when planning meals.


RECIPE MODEL

Fields:

name: str
meal_type: breakfast | lunch | dinner
servings: int
prep_time_minutes: int
ingredients: list[RecipeIngredient]


RECIPE INGREDIENT MODEL

Fields:

ingredient_name: str
quantity: float
unit: str


Ingredient quantities refer to the entire recipe and must be scalable.


INVENTORY SERVICE

Responsibilities:

- Load inventory.json
- Remove expired items
- Aggregate available quantities
- Convert units to normalized system


RECIPE SERVICE

Responsibilities:

- Load recipes.json
- Provide recipe scaling
- Calculate ingredient needs for a given number of servings


MEAL PLANNER SERVICE

Input parameters:

days_to_cover
allow_same_meal_same_day: bool
allow_recipe_repetition: bool
optimization_goal

Optimization goals may include:

minimize_shopping
minimize_prep_time
use_expiring_food


Planning rules:

- 3 meals per day
- total_meals = days_to_cover * 3
- recipes can be scaled
- cooking a recipe can generate multiple servings
- leftovers can be consumed in later meals

Recipe selection algorithm:

1. Load recipes
2. Evaluate inventory
3. Select recipes iteratively until all meals are covered
4. Prefer recipes that maximize usage of available ingredients
5. Apply optimization goal when selecting between recipes


SHOPPING LIST SERVICE

Steps:

1. Calculate total ingredient requirements from the meal plan
2. Compare required ingredients vs available inventory
3. Determine missing quantities
4. Generate shopping list entries


PARTIAL INVENTORY RULE

If recipe requires:

100g sugar

and inventory has:

50g sugar

Shopping list should contain:

50g sugar


PACKAGE SIZE SELECTION

Products database contains possible purchasable packages.

If multiple package sizes exist:

Example:

sugar
1kg package
150g package

If required quantity = 50g

choose the smallest package that satisfies the requirement.

If only one package size exists, select that package.


SHOPPING LIST MODEL

ShoppingListItem fields:

product_barcode
product_name
quantity_to_buy
unit
estimated_price


CLI INTERFACE

The system must be runnable from the command line:

python main.py --days 5

Optional flags:

--allow-repeat-same-day
--allow-recipe-repetition
--optimize minimize_shopping
--optimize minimize_prep_time
--optimize use_expiring_food


OUTPUT

The program prints:

Meal Plan

Day 1
Breakfast: recipe_name
Lunch: recipe_name
Dinner: recipe_name


Shopping List

product_name - quantity - unit


FILE OUTPUT

The shopping list must also be saved as a file.

Location:

outputs/shopping_lists/

Filename format:

shopping_list_{days}days_{timestamp}.csv

Example:

shopping_list_5days_2026-03-14_18-32.csv


CSV format:

product_name,quantity,unit,barcode


JSON DATA FILES

recipes.json

Contains all recipes.

products.json

Contains all purchasable food products with barcodes and package sizes.

inventory.json

Contains current inventory items.


EDGE CASES

Handle:

- expired inventory
- missing ingredients
- unit conversion mismatches
- recipes that cannot be satisfied
- empty inventory


IMPLEMENTATION NOTES

Use dataclasses for models.

Keep services separated from models.

Use clear functions for:

calculate_recipe_requirements()
select_recipes_for_meal_plan()
calculate_missing_ingredients()
generate_shopping_list()


The code should be modular and easy to extend later with:

- barcode scanning
- database persistence
- web interface
- nutrition optimization
"""
import argparse
import csv
from datetime import datetime
from cli.cli_parser import parse_cli_arguments
from services.inventory_service import InventoryService
from services.recipe_service import RecipeService
from services.meal_planner_service import MealPlannerService
from services.shopping_service import ShoppingService



def main():
    """
    Main entry point for the meal planner application.
    """
    try:
        args = parse_cli_arguments()

        inventory_service = InventoryService()
        recipe_service = RecipeService()
        meal_planner = MealPlannerService(inventory_service, recipe_service)
        shopping_service = ShoppingService(recipe_service, inventory_service)

        meal_plan = meal_planner.plan_meals(**args)

        # Print meal plan
        print("Meal Plan")
        for day, meals in meal_plan.items():
            print(f"Day {day}")
            print(f"Breakfast: {meals.breakfast}")
            print(f"Lunch: {meals.lunch}")
            print(f"Dinner: {meals.dinner}")
            print()

        missing = shopping_service.calculate_missing_ingredients(meal_plan)
        shopping_list = shopping_service.generate_shopping_list(missing)

        # Print shopping list
        print("Shopping List")
        for item in shopping_list:
            print(f"{item.product_name} - {item.quantity_to_buy} - {item.unit}")

        # Save CSV
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"outputs/shopping_lists/shopping_list_{args['days_to_cover']}days_{timestamp}.csv"
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["product_name", "quantity", "unit", "barcode"])
            for item in shopping_list:
                writer.writerow([item.product_name, item.quantity_to_buy, item.unit, item.product_barcode])
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
