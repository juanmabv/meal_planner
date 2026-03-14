from dataclasses import dataclass
from datetime import datetime
from typing import Literal

StorageLocation = Literal["pantry", "fridge", "freezer"]

@dataclass
class InventoryItem:
    """
    Represents a specific item in the user's inventory.

    Attributes:
        barcode (str): Barcode of the product.
        quantity (float): Quantity of the item.
        unit (str): Unit of the quantity.
        purchase_date (datetime): Date when the item was purchased.
        opened_date (datetime | None): Date when the item was opened, or None if not opened.
        expiration_date (datetime): Expiration date of the item.
        storage_location (StorageLocation): Where the item is stored.
    """
    barcode: str
    quantity: float
    unit: str
    purchase_date: datetime
    opened_date: datetime | None
    expiration_date: datetime
    storage_location: StorageLocation
