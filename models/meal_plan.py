from dataclasses import dataclass
from typing import Dict, Literal

MealType = Literal["breakfast", "lunch", "dinner"]

@dataclass
class MealDay:
    """
    Represents meals for a single day.

    Attributes:
        breakfast (str): Name of the breakfast recipe.
        lunch (str): Name of the lunch recipe.
        dinner (str): Name of the dinner recipe.
    """
    breakfast: str
    lunch: str
    dinner: str

MealPlan = Dict[int, MealDay]  # Key is day number (1-based)
