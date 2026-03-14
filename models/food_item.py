from dataclasses import dataclass
from typing import Literal

UnitType = Literal["weight", "volume", "count"]

@dataclass
class FoodItem:
    """
    Represents a purchasable food product.

    Attributes:
        barcode (str): Unique identifier for the product.
        name (str): Name of the product.
        category (str): Category of the product (e.g., dairy, grains).
        unit_type (UnitType): Type of unit (weight, volume, or count).
        package_quantity (float): Quantity in the package.
        package_unit (str): Unit of the package quantity (e.g., kg, liters).
        serving_size (float): Size of one serving.
        serving_unit (str): Unit of the serving size.
        price (float | None): Price of the package, or None if unknown.
    """
    barcode: str
    name: str
    category: str
    unit_type: UnitType
    package_quantity: float
    package_unit: str
    serving_size: float
    serving_unit: str
    price: float | None
