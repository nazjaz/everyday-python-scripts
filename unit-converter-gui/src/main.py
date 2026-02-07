"""Unit Converter GUI.

A Python script that creates a simple unit converter with GUI, converting
between different units of length, weight, temperature, and currency.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/converter.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    logger.error("tkinter is not available. Please install python3-tk package.")
    sys.exit(1)


class UnitConverter:
    """Handles unit conversions for different measurement types."""

    LENGTH_CONVERSIONS = {
        "meter": 1.0,
        "kilometer": 1000.0,
        "centimeter": 0.01,
        "millimeter": 0.001,
        "mile": 1609.34,
        "yard": 0.9144,
        "foot": 0.3048,
        "inch": 0.0254,
    }

    WEIGHT_CONVERSIONS = {
        "kilogram": 1.0,
        "gram": 0.001,
        "pound": 0.453592,
        "ounce": 0.0283495,
        "ton": 1000.0,
        "stone": 6.35029,
    }

    TEMPERATURE_CONVERSIONS = {
        "celsius": "celsius",
        "fahrenheit": "fahrenheit",
        "kelvin": "kelvin",
    }

    def __init__(self, currency_rates: Optional[Dict[str, float]] = None) -> None:
        """Initialize the converter with currency exchange rates.

        Args:
            currency_rates: Dictionary mapping currency codes to USD rates
        """
        self.currency_rates = currency_rates or {
            "USD": 1.0,
            "EUR": 0.85,
            "GBP": 0.73,
            "JPY": 110.0,
            "CAD": 1.25,
            "AUD": 1.35,
            "CHF": 0.92,
            "CNY": 6.45,
        }

    def convert_length(
        self, value: float, from_unit: str, to_unit: str
    ) -> Optional[float]:
        """Convert length between units.

        Args:
            value: Value to convert
            from_unit: Source unit name
            to_unit: Target unit name

        Returns:
            Converted value or None if units are invalid
        """
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()

        if from_unit not in self.LENGTH_CONVERSIONS:
            return None
        if to_unit not in self.LENGTH_CONVERSIONS:
            return None

        meters = value * self.LENGTH_CONVERSIONS[from_unit]
        result = meters / self.LENGTH_CONVERSIONS[to_unit]

        return result

    def convert_weight(
        self, value: float, from_unit: str, to_unit: str
    ) -> Optional[float]:
        """Convert weight between units.

        Args:
            value: Value to convert
            from_unit: Source unit name
            to_unit: Target unit name

        Returns:
            Converted value or None if units are invalid
        """
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()

        if from_unit not in self.WEIGHT_CONVERSIONS:
            return None
        if to_unit not in self.WEIGHT_CONVERSIONS:
            return None

        kilograms = value * self.WEIGHT_CONVERSIONS[from_unit]
        result = kilograms / self.WEIGHT_CONVERSIONS[to_unit]

        return result

    def convert_temperature(
        self, value: float, from_unit: str, to_unit: str
    ) -> Optional[float]:
        """Convert temperature between units.

        Args:
            value: Value to convert
            from_unit: Source unit name
            to_unit: Target unit name

        Returns:
            Converted value or None if units are invalid
        """
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()

        if from_unit not in self.TEMPERATURE_CONVERSIONS:
            return None
        if to_unit not in self.TEMPERATURE_CONVERSIONS:
            return None

        if from_unit == to_unit:
            return value

        celsius = self._to_celsius(value, from_unit)
        result = self._from_celsius(celsius, to_unit)

        return result

    def _to_celsius(self, value: float, unit: str) -> float:
        """Convert temperature to Celsius.

        Args:
            value: Temperature value
            unit: Source unit

        Returns:
            Temperature in Celsius
        """
        if unit == "celsius":
            return value
        elif unit == "fahrenheit":
            return (value - 32) * 5 / 9
        elif unit == "kelvin":
            return value - 273.15
        return value

    def _from_celsius(self, value: float, unit: str) -> float:
        """Convert temperature from Celsius.

        Args:
            value: Temperature in Celsius
            unit: Target unit

        Returns:
            Converted temperature
        """
        if unit == "celsius":
            return value
        elif unit == "fahrenheit":
            return (value * 9 / 5) + 32
        elif unit == "kelvin":
            return value + 273.15
        return value

    def convert_currency(
        self, value: float, from_currency: str, to_currency: str
    ) -> Optional[float]:
        """Convert currency between units.

        Args:
            value: Value to convert
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Converted value or None if currencies are invalid
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency not in self.currency_rates:
            return None
        if to_currency not in self.currency_rates:
            return None

        usd_value = value / self.currency_rates[from_currency]
        result = usd_value * self.currency_rates[to_currency]

        return result

    def update_currency_rates(self, rates: Dict[str, float]) -> None:
        """Update currency exchange rates.

        Args:
            rates: Dictionary mapping currency codes to USD rates
        """
        self.currency_rates.update(rates)
        logger.info(f"Updated currency rates: {len(rates)} currencies")


class ConverterGUI:
    """GUI application for unit conversion."""

    def __init__(self, converter: UnitConverter, currency_rates_file: Optional[Path] = None) -> None:
        """Initialize the GUI application.

        Args:
            converter: UnitConverter instance
            currency_rates_file: Optional path to currency rates JSON file
        """
        self.converter = converter
        self.currency_rates_file = currency_rates_file
        self.root = tk.Tk()
        self.root.title("Unit Converter")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up the user interface."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        category_label = ttk.Label(main_frame, text="Category:")
        category_label.grid(row=0, column=0, sticky=tk.W, pady=5)

        self.category_var = tk.StringVar(value="Length")
        category_combo = ttk.Combobox(
            main_frame,
            textvariable=self.category_var,
            values=["Length", "Weight", "Temperature", "Currency"],
            state="readonly",
            width=20,
        )
        category_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        category_combo.bind("<<ComboboxSelected>>", self.on_category_change)

        from_label = ttk.Label(main_frame, text="From:")
        from_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        self.from_var = tk.StringVar()
        self.from_combo = ttk.Combobox(
            main_frame, textvariable=self.from_var, state="readonly", width=20
        )
        self.from_combo.grid(row=1, column=1, sticky=tk.W, pady=5)

        value_label = ttk.Label(main_frame, text="Value:")
        value_label.grid(row=2, column=0, sticky=tk.W, pady=5)

        self.value_var = tk.StringVar()
        value_entry = ttk.Entry(main_frame, textvariable=self.value_var, width=23)
        value_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        value_entry.bind("<KeyRelease>", self.on_value_change)

        to_label = ttk.Label(main_frame, text="To:")
        to_label.grid(row=3, column=0, sticky=tk.W, pady=5)

        self.to_var = tk.StringVar()
        self.to_combo = ttk.Combobox(
            main_frame, textvariable=self.to_var, state="readonly", width=20
        )
        self.to_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        self.to_combo.bind("<<ComboboxSelected>>", self.on_unit_change)

        result_label = ttk.Label(main_frame, text="Result:")
        result_label.grid(row=4, column=0, sticky=tk.W, pady=5)

        self.result_var = tk.StringVar(value="0.00")
        result_entry = ttk.Entry(
            main_frame, textvariable=self.result_var, state="readonly", width=23
        )
        result_entry.grid(row=4, column=1, sticky=tk.W, pady=5)

        convert_button = ttk.Button(
            main_frame, text="Convert", command=self.perform_conversion
        )
        convert_button.grid(row=5, column=0, columnspan=2, pady=20)

        clear_button = ttk.Button(
            main_frame, text="Clear", command=self.clear_fields
        )
        clear_button.grid(row=6, column=0, columnspan=2, pady=5)

        self.on_category_change()

    def on_category_change(self, event=None) -> None:
        """Handle category selection change."""
        category = self.category_var.get()

        if category == "Length":
            units = list(self.converter.LENGTH_CONVERSIONS.keys())
        elif category == "Weight":
            units = list(self.converter.WEIGHT_CONVERSIONS.keys())
        elif category == "Temperature":
            units = list(self.converter.TEMPERATURE_CONVERSIONS.keys())
        elif category == "Currency":
            units = list(self.converter.currency_rates.keys())
        else:
            units = []

        self.from_combo["values"] = units
        self.to_combo["values"] = units

        if units:
            self.from_var.set(units[0])
            self.to_var.set(units[1] if len(units) > 1 else units[0])

        self.clear_fields()

    def on_value_change(self, event=None) -> None:
        """Handle value input change."""
        self.perform_conversion()

    def on_unit_change(self, event=None) -> None:
        """Handle unit selection change."""
        self.perform_conversion()

    def perform_conversion(self) -> None:
        """Perform the unit conversion."""
        try:
            value_str = self.value_var.get().strip()
            if not value_str:
                self.result_var.set("0.00")
                return

            value = float(value_str)
            category = self.category_var.get()
            from_unit = self.from_var.get()
            to_unit = self.to_var.get()

            if not from_unit or not to_unit:
                return

            result = None

            if category == "Length":
                result = self.converter.convert_length(value, from_unit, to_unit)
            elif category == "Weight":
                result = self.converter.convert_weight(value, from_unit, to_unit)
            elif category == "Temperature":
                result = self.converter.convert_temperature(value, from_unit, to_unit)
            elif category == "Currency":
                result = self.converter.convert_currency(value, from_unit, to_unit)

            if result is not None:
                self.result_var.set(f"{result:.6f}".rstrip("0").rstrip("."))
            else:
                self.result_var.set("Error")

        except ValueError:
            self.result_var.set("Invalid input")
        except Exception as e:
            logger.exception(f"Error during conversion: {e}")
            self.result_var.set("Error")

    def clear_fields(self) -> None:
        """Clear all input fields."""
        self.value_var.set("")
        self.result_var.set("0.00")

    def run(self) -> None:
        """Start the GUI application."""
        self.root.mainloop()


def load_currency_rates(rates_file: Path) -> Dict[str, float]:
    """Load currency exchange rates from JSON file.

    Args:
        rates_file: Path to JSON file with currency rates

    Returns:
        Dictionary mapping currency codes to USD rates

    Raises:
        FileNotFoundError: If rates file does not exist
        json.JSONDecodeError: If JSON is invalid
    """
    if not rates_file.exists():
        raise FileNotFoundError(f"Currency rates file not found: {rates_file}")

    try:
        with open(rates_file, "r") as f:
            rates = json.load(f)
        return rates
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in rates file: {e}")
        raise


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary containing configuration values

    Raises:
        FileNotFoundError: If config file does not exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config if config else {}
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config file: {e}")
        raise


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="Unit converter GUI application"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML)",
    )
    parser.add_argument(
        "--currency-rates",
        type=str,
        default=None,
        help="Path to currency rates JSON file",
    )

    args = parser.parse_args()

    try:
        currency_rates = None
        currency_rates_file = None

        if args.config:
            config = load_config(Path(args.config))
            if "currency_rates_file" in config:
                currency_rates_file = Path(config["currency_rates_file"])
            if "currency_rates" in config:
                currency_rates = config["currency_rates"]

        if args.currency_rates:
            currency_rates_file = Path(args.currency_rates)

        if currency_rates_file and currency_rates_file.exists():
            currency_rates = load_currency_rates(currency_rates_file)

        converter = UnitConverter(currency_rates=currency_rates)
        app = ConverterGUI(converter, currency_rates_file)
        app.run()

        return 0

    except (ValueError, FileNotFoundError) as e:
        logger.error(f"Error: {e}")
        messagebox.showerror("Error", f"Application error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        messagebox.showerror("Error", f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
