"""Unit tests for unit converter GUI."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.main import (
    UnitConverter,
    load_config,
    load_currency_rates,
)


class TestUnitConverter:
    """Test UnitConverter class."""

    def test_init_default_rates(self):
        """Test initialization with default currency rates."""
        converter = UnitConverter()
        assert "USD" in converter.currency_rates
        assert converter.currency_rates["USD"] == 1.0

    def test_init_custom_rates(self):
        """Test initialization with custom currency rates."""
        custom_rates = {"USD": 1.0, "EUR": 0.85, "GBP": 0.73}
        converter = UnitConverter(currency_rates=custom_rates)
        assert converter.currency_rates == custom_rates

    def test_convert_length_meter_to_kilometer(self):
        """Test length conversion from meters to kilometers."""
        converter = UnitConverter()
        result = converter.convert_length(1000, "meter", "kilometer")
        assert result == pytest.approx(1.0)

    def test_convert_length_mile_to_meter(self):
        """Test length conversion from miles to meters."""
        converter = UnitConverter()
        result = converter.convert_length(1, "mile", "meter")
        assert result == pytest.approx(1609.34)

    def test_convert_length_invalid_unit(self):
        """Test length conversion with invalid unit returns None."""
        converter = UnitConverter()
        result = converter.convert_length(100, "invalid", "meter")
        assert result is None

    def test_convert_weight_kilogram_to_pound(self):
        """Test weight conversion from kilograms to pounds."""
        converter = UnitConverter()
        result = converter.convert_weight(1, "kilogram", "pound")
        assert result == pytest.approx(2.20462, rel=1e-4)

    def test_convert_weight_pound_to_gram(self):
        """Test weight conversion from pounds to grams."""
        converter = UnitConverter()
        result = converter.convert_weight(1, "pound", "gram")
        assert result == pytest.approx(453.592)

    def test_convert_weight_invalid_unit(self):
        """Test weight conversion with invalid unit returns None."""
        converter = UnitConverter()
        result = converter.convert_weight(100, "invalid", "kilogram")
        assert result is None

    def test_convert_temperature_celsius_to_fahrenheit(self):
        """Test temperature conversion from Celsius to Fahrenheit."""
        converter = UnitConverter()
        result = converter.convert_temperature(0, "celsius", "fahrenheit")
        assert result == pytest.approx(32.0)

    def test_convert_temperature_fahrenheit_to_celsius(self):
        """Test temperature conversion from Fahrenheit to Celsius."""
        converter = UnitConverter()
        result = converter.convert_temperature(32, "fahrenheit", "celsius")
        assert result == pytest.approx(0.0)

    def test_convert_temperature_celsius_to_kelvin(self):
        """Test temperature conversion from Celsius to Kelvin."""
        converter = UnitConverter()
        result = converter.convert_temperature(0, "celsius", "kelvin")
        assert result == pytest.approx(273.15)

    def test_convert_temperature_kelvin_to_celsius(self):
        """Test temperature conversion from Kelvin to Celsius."""
        converter = UnitConverter()
        result = converter.convert_temperature(273.15, "kelvin", "celsius")
        assert result == pytest.approx(0.0)

    def test_convert_temperature_same_unit(self):
        """Test temperature conversion with same unit returns same value."""
        converter = UnitConverter()
        result = converter.convert_temperature(100, "celsius", "celsius")
        assert result == 100.0

    def test_convert_temperature_invalid_unit(self):
        """Test temperature conversion with invalid unit returns None."""
        converter = UnitConverter()
        result = converter.convert_temperature(100, "invalid", "celsius")
        assert result is None

    def test_convert_currency_usd_to_eur(self):
        """Test currency conversion from USD to EUR."""
        converter = UnitConverter(currency_rates={"USD": 1.0, "EUR": 0.85})
        result = converter.convert_currency(100, "USD", "EUR")
        assert result == pytest.approx(85.0)

    def test_convert_currency_eur_to_usd(self):
        """Test currency conversion from EUR to USD."""
        converter = UnitConverter(currency_rates={"USD": 1.0, "EUR": 0.85})
        result = converter.convert_currency(85, "EUR", "USD")
        assert result == pytest.approx(100.0)

    def test_convert_currency_case_insensitive(self):
        """Test currency conversion is case insensitive."""
        converter = UnitConverter(currency_rates={"USD": 1.0, "EUR": 0.85})
        result1 = converter.convert_currency(100, "usd", "eur")
        result2 = converter.convert_currency(100, "USD", "EUR")
        assert result1 == result2

    def test_convert_currency_invalid_currency(self):
        """Test currency conversion with invalid currency returns None."""
        converter = UnitConverter(currency_rates={"USD": 1.0, "EUR": 0.85})
        result = converter.convert_currency(100, "INVALID", "EUR")
        assert result is None

    def test_update_currency_rates(self):
        """Test updating currency rates."""
        converter = UnitConverter(currency_rates={"USD": 1.0, "EUR": 0.85})
        converter.update_currency_rates({"GBP": 0.73, "JPY": 110.0})
        assert "GBP" in converter.currency_rates
        assert "JPY" in converter.currency_rates
        assert converter.currency_rates["GBP"] == 0.73


class TestLoadCurrencyRates:
    """Test currency rates loading."""

    def test_load_currency_rates_valid_json(self):
        """Test loading valid currency rates JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            rates_data = {"USD": 1.0, "EUR": 0.85, "GBP": 0.73}
            json.dump(rates_data, f)
            rates_file = Path(f.name)

        try:
            result = load_currency_rates(rates_file)
            assert result == rates_data
        finally:
            rates_file.unlink()

    def test_load_currency_rates_file_not_found(self):
        """Test that missing rates file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_currency_rates(Path("/nonexistent/rates.json"))

    def test_load_currency_rates_invalid_json(self):
        """Test that invalid JSON raises JSONDecodeError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content {")
            rates_file = Path(f.name)

        try:
            with pytest.raises(json.JSONDecodeError):
                load_currency_rates(rates_file)
        finally:
            rates_file.unlink()


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_config_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "currency_rates_file": "./currency_rates.json",
                "currency_rates": {"USD": 1.0, "EUR": 0.85},
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            result = load_config(config_path)
            assert result["currency_rates_file"] == "./currency_rates.json"
            assert result["currency_rates"]["USD"] == 1.0
        finally:
            config_path.unlink()

    def test_load_config_file_not_found(self):
        """Test that missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))

    def test_load_config_invalid_yaml(self):
        """Test that invalid YAML raises YAMLError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = Path(f.name)

        try:
            with pytest.raises(yaml.YAMLError):
                load_config(config_path)
        finally:
            config_path.unlink()


class TestConversionAccuracy:
    """Test conversion accuracy for various units."""

    def test_length_conversions_round_trip(self):
        """Test that length conversions are reversible."""
        converter = UnitConverter()
        original_value = 100.0

        for unit in converter.LENGTH_CONVERSIONS.keys():
            converted = converter.convert_length(original_value, "meter", unit)
            back = converter.convert_length(converted, unit, "meter")
            assert back == pytest.approx(original_value, rel=1e-6)

    def test_weight_conversions_round_trip(self):
        """Test that weight conversions are reversible."""
        converter = UnitConverter()
        original_value = 100.0

        for unit in converter.WEIGHT_CONVERSIONS.keys():
            converted = converter.convert_weight(original_value, "kilogram", unit)
            back = converter.convert_weight(converted, unit, "kilogram")
            assert back == pytest.approx(original_value, rel=1e-6)

    def test_temperature_conversions_known_values(self):
        """Test temperature conversions with known values."""
        converter = UnitConverter()

        assert converter.convert_temperature(0, "celsius", "fahrenheit") == pytest.approx(32.0)
        assert converter.convert_temperature(100, "celsius", "fahrenheit") == pytest.approx(212.0)
        assert converter.convert_temperature(-40, "celsius", "fahrenheit") == pytest.approx(-40.0)
        assert converter.convert_temperature(0, "celsius", "kelvin") == pytest.approx(273.15)
