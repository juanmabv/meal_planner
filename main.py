"""Meal planner application.

This project provides a CLI for generating meal plans and shopping lists, and also includes
Tkinter-based GUIs for editing the product catalog and managing inventory.

Run the product editor GUI:
    python services/food_item_creator.py

Run the inventory manager GUI:
    python services/inventory_manager.py

Run the (work-in-progress) CLI planner:
    python main.py --days 7
"""

from __future__ import annotations

from cli.cli_parser import parse_cli_arguments


def main() -> None:
    """Entry point for the meal planning application."""
    args = parse_cli_arguments()

    if args.get("gui"):
        # Launch the product editor GUI
        from services.food_item_creator import main as run_editor

        run_editor()
        return

    # CLI planner is intentionally minimal in this workspace.
    print("CLI planner is not implemented in this workspace yet.")
    print("Use `python services/food_item_creator.py` to edit food products.")
    print("Use `python services/inventory_manager.py` to manage inventory.")


if __name__ == "__main__":
    main()