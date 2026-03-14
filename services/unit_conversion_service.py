from typing import Dict

class UnitConversionService:
    """
    Service for handling unit conversions to normalized International System units.

    Normalized units:
    - Weight: kilograms (kg)
    - Volume: liters (l)
    - Count: count (no change)
    """

    # Conversion factors to normalized units
    WEIGHT_CONVERSIONS: Dict[str, float] = {
        "kg": 1.0,
        "g": 0.001,
        "grams": 0.001,
        "kilograms": 1.0,
        # Add more if needed, e.g., "lb": 0.453592, "oz": 0.0283495
    }

    VOLUME_CONVERSIONS: Dict[str, float] = {
        "l": 1.0,
        "liters": 1.0,
        "ml": 0.001,
        "milliliters": 0.001,
        # Add more if needed
    }

    COUNT_UNITS = {"count", "pieces", "items"}

    @staticmethod
    def get_unit_type(unit: str) -> str:
        """
        Determines the type of unit: weight, volume, or count.

        Args:
            unit (str): The unit to check.

        Returns:
            str: "weight", "volume", or "count".
        """
        unit_lower = unit.lower()
        if unit_lower in UnitConversionService.WEIGHT_CONVERSIONS:
            return "weight"
        elif unit_lower in UnitConversionService.VOLUME_CONVERSIONS:
            return "volume"
        elif unit_lower in UnitConversionService.COUNT_UNITS:
            return "count"
        else:
            raise ValueError(f"Unknown unit: {unit}")

    @staticmethod
    def normalize_quantity(quantity: float, unit: str) -> tuple[float, str]:
        """
        Normalizes the quantity to the standard unit for its type.

        Args:
            quantity (float): The quantity to normalize.
            unit (str): The unit of the quantity.

        Returns:
            tuple[float, str]: Normalized quantity and normalized unit.
        """
        unit_type = UnitConversionService.get_unit_type(unit)
        if unit_type == "weight":
            factor = UnitConversionService.WEIGHT_CONVERSIONS.get(unit.lower(), 1.0)
            return quantity * factor, "kg"
        elif unit_type == "volume":
            factor = UnitConversionService.VOLUME_CONVERSIONS.get(unit.lower(), 1.0)
            return quantity * factor, "l"
        else:  # count
            return quantity, "count"

    @staticmethod
    def convert_to_unit(quantity: float, from_unit: str, to_unit: str) -> float:
        """
        Converts quantity from one unit to another.

        Args:
            quantity (float): The quantity to convert.
            from_unit (str): The source unit.
            to_unit (str): The target unit.

        Returns:
            float: The converted quantity.
        """
        # First normalize to standard
        norm_qty, norm_unit = UnitConversionService.normalize_quantity(quantity, from_unit)
        # Then convert to target
        if norm_unit == to_unit:
            return norm_qty
        # If target is not standard, need reverse conversion
        # For simplicity, assume to_unit is standard or known
        if to_unit.lower() in UnitConversionService.WEIGHT_CONVERSIONS:
            factor = UnitConversionService.WEIGHT_CONVERSIONS[to_unit.lower()]
            return norm_qty / factor
        elif to_unit.lower() in UnitConversionService.VOLUME_CONVERSIONS:
            factor = UnitConversionService.VOLUME_CONVERSIONS[to_unit.lower()]
            return norm_qty / factor
        else:
            return norm_qty  # for count
