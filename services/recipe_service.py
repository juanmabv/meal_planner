import json
from typing import Dict, List, Tuple
from pathlib import Path

from models.recipe import Recipe
from models.recipe_ingredient import RecipeIngredient

class RecipeService:
    """
    Service for managing recipes.

    Responsibilities:
    - Load recipes from JSON
    - Scale recipes
    - Calculate ingredient requirements
    """

    def __init__(self, recipes_file: str = "data/recipes.json"):
        self.recipes_file = Path(recipes_file)
        self._recipes: Dict[str, Recipe] = {}
        self._load_recipes()

    def _load_recipes(self):
        """Loads recipes from JSON file."""
        with open(self.recipes_file, 'r') as f:
            data = json.load(f)
        for recipe_data in data:
            ingredients = [
                RecipeIngredient(
                    ingredient_name=ing['ingredient_name'],
                    quantity=ing['quantity'],
                    unit=ing['unit']
                ) for ing in recipe_data['ingredients']
            ]
            recipe = Recipe(
                name=recipe_data['name'],
                meal_type=recipe_data['meal_type'],
                servings=recipe_data['servings'],
                prep_time_minutes=recipe_data['prep_time_minutes'],
                ingredients=ingredients
            )
            self._recipes[recipe.name] = recipe

    def get_recipe(self, name: str) -> Recipe | None:
        """
        Gets a recipe by name.

        Args:
            name (str): Name of the recipe.

        Returns:
            Recipe | None: The recipe if found.
        """
        return self._recipes.get(name)

    def get_all_recipes(self) -> List[Recipe]:
        """
        Gets all recipes.

        Returns:
            List[Recipe]: List of all recipes.
        """
        return list(self._recipes.values())

    def scale_recipe(self, recipe: Recipe, target_servings: int) -> Recipe:
        """
        Scales a recipe to a different number of servings.

        Args:
            recipe (Recipe): The original recipe.
            target_servings (int): Target number of servings.

        Returns:
            Recipe: Scaled recipe.
        """
        scale_factor = target_servings / recipe.servings
        scaled_ingredients = [
            RecipeIngredient(
                ingredient_name=ing.ingredient_name,
                quantity=ing.quantity * scale_factor,
                unit=ing.unit
            ) for ing in recipe.ingredients
        ]
        return Recipe(
            name=recipe.name,
            meal_type=recipe.meal_type,
            servings=target_servings,
            prep_time_minutes=recipe.prep_time_minutes,  # Assume prep time doesn't scale
            ingredients=scaled_ingredients
        )

    def calculate_ingredient_requirements(self, recipe_name: str, num_servings: int) -> Dict[str, Tuple[float, str]]:
        """
        Calculates ingredient requirements for a recipe scaled to num_servings.

        Args:
            recipe_name (str): Name of the recipe.
            num_servings (int): Number of servings.

        Returns:
            Dict[str, Tuple[float, str]]: Ingredient name to (quantity, unit).
        """
        recipe = self.get_recipe(recipe_name)
        if not recipe:
            raise ValueError(f"Recipe {recipe_name} not found")
        scaled = self.scale_recipe(recipe, num_servings)
        requirements = {}
        for ing in scaled.ingredients:
            requirements[ing.ingredient_name] = (ing.quantity, ing.unit)
        return requirements
