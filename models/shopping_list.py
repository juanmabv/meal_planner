from dataclasses import dataclass
from typing import List

@dataclass
class ShoppingListItem:
    """
    Represents an item in the shopping list.

    Attributes:
        product_barcode (str): Barcode of the product.
        product_name (str): Name of the product.
        quantity_to_buy (float): Quantity to buy.
        unit (str): Unit of the quantity.
        estimated_price (float): Estimated price for the quantity.
    """
    product_barcode: str
    product_name: str
    quantity_to_buy: float
    unit: str
    estimated_price: float

ShoppingList = List[ShoppingListItem]
