import argparse
from typing import Dict, Any

def parse_cli_arguments() -> Dict[str, Any]:
    """Parses command line arguments for the meal planner.

    Returns:
        Dict[str, Any]: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Meal Planning and Grocery Optimization System")
    parser.add_argument("--days", type=int, required=False, help="Number of days to cover")
    parser.add_argument("--allow-repeat-same-day", action="store_true", help="Allow same recipe for different meals in the same day")
    parser.add_argument("--allow-recipe-repetition", action="store_true", help="Allow repeating recipes across days")
    parser.add_argument(
        "--optimize",
        choices=["minimize_shopping", "minimize_prep_time", "use_expiring_food"],
        default="minimize_shopping",
        help="Optimization goal",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the GUI editor for food products",
    )

    args = parser.parse_args()
    return {
        "days_to_cover": args.days,
        "allow_same_meal_same_day": args.allow_repeat_same_day,
        "allow_recipe_repetition": args.allow_recipe_repetition,
        "optimization_goal": args.optimize,
        "gui": args.gui,
    }
