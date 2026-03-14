import json
from datetime import datetime
from typing import Dict, List
from pathlib import Path

from models.inventory_item import InventoryItem
from services.unit_conversion_service import UnitConversionService

class InventoryService:
    """
    Service for managing inventory data.

    Responsibilities:
    - Load inventory from JSON
    - Filter out expired items
    - Aggregate quantities by barcode in normalized units
    """

    def __init__(self, inventory_file: str = "data/inventory.json"):
        self.inventory_file = Path(inventory_file)

    def load_inventory(self) -> List[InventoryItem]:
        """
        Loads inventory items from JSON file.

        Returns:
            List[InventoryItem]: List of inventory items.
        """
        with open(self.inventory_file, 'r') as f:
            data = json.load(f)
        inventory = []
        for item_data in data:
            # Parse dates
            purchase_date = datetime.fromisoformat(item_data['purchase_date'])
            opened_date = datetime.fromisoformat(item_data['opened_date']) if item_data['opened_date'] else None
            expiration_date = datetime.fromisoformat(item_data['expiration_date'])
            item = InventoryItem(
                barcode=item_data['barcode'],
                quantity=item_data['quantity'],
                unit=item_data['unit'],
                purchase_date=purchase_date,
                opened_date=opened_date,
                expiration_date=expiration_date,
                storage_location=item_data['storage_location']
            )
            inventory.append(item)
        return inventory

    def get_available_inventory(self) -> Dict[str, float]:
        """
        Gets aggregated available inventory quantities in normalized units, excluding expired items.

        Returns:
            Dict[str, float]: Barcode to total normalized quantity.
        """
        inventory = self.load_inventory()
        now = datetime.now()
        available = {}
        for item in inventory:
            if item.expiration_date > now:
                norm_qty, _ = UnitConversionService.normalize_quantity(item.quantity, item.unit)
                if item.barcode in available:
                    available[item.barcode] += norm_qty
                else:
                    available[item.barcode] = norm_qty
        return available
