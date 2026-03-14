from dataclasses import dataclass

@dataclass
class RecipeIngredient:
    """
    Represents an ingredient in a recipe.

    Attributes:
        ingredient_name (str): Name of the ingredient.
        quantity (float): Quantity required.
        unit (str): Unit of the quantity.
    """
    ingredient_name: str
    quantity: float
    unit: str
