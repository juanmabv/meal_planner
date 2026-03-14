from dataclasses import dataclass
from typing import Literal
from .recipe_ingredient import RecipeIngredient

MealType = Literal["breakfast", "lunch", "dinner"]

@dataclass
class Recipe:
    """
    Represents a recipe.

    Attributes:
        name (str): Name of the recipe.
        meal_type (MealType): Type of meal (breakfast, lunch, dinner).
        servings (int): Number of servings the recipe makes.
        prep_time_minutes (int): Preparation time in minutes.
        ingredients (list[RecipeIngredient]): List of ingredients required.
    """
    name: str
    meal_type: MealType
    servings: int
    prep_time_minutes: int
    ingredients: list[RecipeIngredient]
