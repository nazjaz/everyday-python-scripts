"""Weather Scraper - Scrape and display weather information.

This module provides functionality to scrape weather information from public
weather websites and display current conditions and forecasts in a GUI application.
"""

import json
import logging
import logging.handlers
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
import yaml
from dotenv import load_dotenv

try:
    from tkinter import (
        Button,
        Entry,
        Frame,
        Label,
        StringVar,
        Tk,
        messagebox,
    )
except ImportError:
    Tk = None
    messagebox = None

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class WeatherScraper:
    """Scrapes weather information from public websites."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize WeatherScraper with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.current_weather: Optional[Dict] = None
        self.forecast: List[Dict] = []
        self.current_city = self.config["location"]["default_city"]
        self.refresh_thread: Optional[threading.Thread] = None
        self.running = False

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid.
        """
        config_file = Path(config_path)

        if not config_file.is_absolute():
            if not config_file.exists():
                parent_config = Path(__file__).parent.parent / config_path
                if parent_config.exists():
                    config_file = parent_config
                else:
                    cwd_config = Path.cwd() / config_path
                    if cwd_config.exists():
                        config_file = cwd_config

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("DEFAULT_CITY"):
            config["location"]["default_city"] = os.getenv("DEFAULT_CITY")
        if os.getenv("DEFAULT_COUNTRY"):
            config["location"]["default_country"] = os.getenv("DEFAULT_COUNTRY")
        if os.getenv("REFRESH_INTERVAL"):
            config["updates"]["refresh_interval"] = int(os.getenv("REFRESH_INTERVAL"))

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/weather_scraper.log")

        log_path = Path(log_file)
        if not log_path.is_absolute():
            project_root = Path(__file__).parent.parent
            log_path = project_root / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers.clear()

        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=log_config.get("max_bytes", 10485760),
            backupCount=log_config.get("backup_count", 5),
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            log_config.get(
                "format",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        logger.info("Logging configured successfully")

    def _fetch_weather_data(self, city: str) -> Optional[Dict]:
        """Fetch weather data for a city.

        Args:
            city: City name to fetch weather for.

        Returns:
            Weather data dictionary or None if fetch failed.
        """
        source_config = self.config.get("weather_source", {})
        provider = source_config.get("provider", "wttr")
        base_url = source_config.get("base_url", "https://wttr.in")
        timeout = source_config.get("timeout", 10)
        user_agent = source_config.get("user_agent", "Weather-Scraper/1.0")

        try:
            if provider == "wttr":
                # Use wttr.in service
                url = f"{base_url}/{city}?format=j1"
                headers = {"User-Agent": user_agent}

                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()

                data = response.json()
                return data

            else:
                logger.error(f"Unknown weather provider: {provider}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing weather data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}", exc_info=True)
            return None

    def _parse_weather_data(self, data: Dict) -> tuple:
        """Parse weather data into current conditions and forecast.

        Args:
            data: Raw weather data dictionary.

        Returns:
            Tuple of (current_weather, forecast_list).
        """
        if not data:
            return None, []

        try:
            # Parse wttr.in JSON format
            current = data.get("current_condition", [{}])[0]
            location = data.get("nearest_area", [{}])[0]

            current_weather = {
                "location": location.get("areaName", [{}])[0].get("value", "Unknown"),
                "country": location.get("country", [{}])[0].get("value", "Unknown"),
                "temperature": current.get("temp_C", "N/A"),
                "feels_like": current.get("FeelsLikeC", "N/A"),
                "condition": current.get("weatherDesc", [{}])[0].get("value", "Unknown"),
                "humidity": current.get("humidity", "N/A"),
                "wind_speed": current.get("windspeedKmph", "N/A"),
                "wind_direction": current.get("winddir16Point", "N/A"),
                "pressure": current.get("pressure", "N/A"),
                "visibility": current.get("visibility", "N/A"),
                "uv_index": current.get("uvIndex", "N/A"),
                "observation_time": current.get("localObsDateTime", "N/A"),
            }

            # Parse forecast
            forecast = []
            forecast_days = self.config.get("display", {}).get("forecast_days", 3)
            weather_data = data.get("weather", [])

            for day_data in weather_data[:forecast_days]:
                date = day_data.get("date", "N/A")
                daily = day_data.get("avgtempC", "N/A")
                max_temp = day_data.get("maxtempC", "N/A")
                min_temp = day_data.get("mintempC", "N/A")
                condition = day_data.get("hourly", [{}])[0].get("weatherDesc", [{}])[0].get("value", "Unknown")

                forecast.append({
                    "date": date,
                    "condition": condition,
                    "max_temp": max_temp,
                    "min_temp": min_temp,
                    "avg_temp": daily,
                })

            return current_weather, forecast

        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Error parsing weather data: {e}")
            return None, []

    def fetch_weather(self, city: Optional[str] = None) -> bool:
        """Fetch and parse weather data for a city.

        Args:
            city: City name (uses current city if None).

        Returns:
            True if successful, False otherwise.
        """
        if city is None:
            city = self.current_city

        logger.info(f"Fetching weather for: {city}")

        data = self._fetch_weather_data(city)
        if not data:
            return False

        current, forecast = self._parse_weather_data(data)
        if current:
            self.current_weather = current
            self.forecast = forecast
            self.current_city = city
            logger.info(f"Weather data fetched successfully for {city}")
            return True

        return False

    def _auto_refresh_loop(self) -> None:
        """Auto-refresh loop for periodic updates."""
        interval = self.config.get("updates", {}).get("refresh_interval", 300)

        while self.running:
            time.sleep(interval)
            if self.running:
                try:
                    self.fetch_weather()
                    if hasattr(self, "root") and self.root:
                        self.root.after(0, self._update_display)
                except Exception as e:
                    logger.error(f"Error in auto-refresh: {e}")

    def _create_main_window(self) -> None:
        """Create main application window."""
        if Tk is None:
            logger.error("tkinter not available")
            return

        self.root = Tk()
        gui_config = self.config.get("gui", {})
        theme = gui_config.get("theme", {})

        self.root.title(gui_config.get("window_title", "Weather Scraper"))
        self.root.geometry(
            f"{gui_config.get('window_width', 600)}x{gui_config.get('window_height', 700)}"
        )
        self.root.configure(bg=theme.get("background_color", "#F0F0F0"))

        # Main container
        main_frame = Frame(self.root, bg=theme.get("background_color", "#F0F0F0"))
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header_frame = Frame(main_frame, bg=theme.get("header_color", "#2C3E50"))
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = Label(
            header_frame,
            text="Weather Information",
            font=("Arial", 18, "bold"),
            bg=theme.get("header_color", "#2C3E50"),
            fg="white",
        )
        title_label.pack(pady=10)

        # City input
        input_frame = Frame(main_frame, bg=theme.get("background_color", "#F0F0F0"))
        input_frame.pack(fill="x", pady=(0, 10))

        Label(
            input_frame,
            text="City:",
            font=("Arial", 10),
            bg=theme.get("background_color", "#F0F0F0"),
            fg=theme.get("text_color", "#333333"),
        ).pack(side="left", padx=(0, 5))

        self.city_var = StringVar(value=self.current_city)
        city_entry = Entry(input_frame, textvariable=self.city_var, width=20, font=("Arial", 10))
        city_entry.pack(side="left", padx=5)

        def refresh_weather():
            city = self.city_var.get().strip()
            if city:
                self.fetch_weather(city)
                self._update_display()

        refresh_button = Button(
            input_frame,
            text="Refresh",
            command=refresh_weather,
            bg=theme.get("button_color", "#3498DB"),
            fg="white",
            font=("Arial", 10),
        )
        refresh_button.pack(side="left", padx=5)

        # Current weather display
        self.current_frame = Frame(main_frame, bg=theme.get("background_color", "#F0F0F0"))
        self.current_frame.pack(fill="both", expand=True, pady=10)

        # Forecast display
        self.forecast_frame = Frame(main_frame, bg=theme.get("background_color", "#F0F0F0"))
        self.forecast_frame.pack(fill="both", expand=True, pady=10)

        # Status label
        self.status_var = StringVar(value="Ready")
        status_label = Label(
            main_frame,
            textvariable=self.status_var,
            font=("Arial", 9),
            bg=theme.get("background_color", "#F0F0F0"),
            fg=theme.get("text_color", "#333333"),
        )
        status_label.pack(pady=5)

        # Initial fetch
        if self.config.get("updates", {}).get("refresh_on_start", True):
            self.fetch_weather()
            self._update_display()

        logger.info("Main window created")

    def _update_display(self) -> None:
        """Update GUI display with current weather data."""
        if not hasattr(self, "current_frame"):
            return

        theme = self.config.get("gui", {}).get("theme", {})
        display_config = self.config.get("display", {})

        # Clear current frame
        for widget in self.current_frame.winfo_children():
            widget.destroy()

        # Clear forecast frame
        for widget in self.forecast_frame.winfo_children():
            widget.destroy()

        if not self.current_weather:
            error_label = Label(
                self.current_frame,
                text="No weather data available.\nEnter a city and click Refresh.",
                font=("Arial", 12),
                bg=theme.get("background_color", "#F0F0F0"),
                fg=theme.get("error_color", "#E74C3C"),
                justify="center",
            )
            error_label.pack(pady=20)
            return

        # Display current weather
        if display_config.get("show_current", True):
            location_text = f"{self.current_weather['location']}, {self.current_weather['country']}"
            location_label = Label(
                self.current_frame,
                text=location_text,
                font=("Arial", 14, "bold"),
                bg=theme.get("background_color", "#F0F0F0"),
                fg=theme.get("text_color", "#333333"),
            )
            location_label.pack(pady=5)

            temp_unit = display_config.get("temperature_unit", "C")
            temp_symbol = "°C" if temp_unit == "C" else "°F"
            temp = self.current_weather.get("temperature", "N/A")
            if temp != "N/A" and temp_unit == "F":
                try:
                    temp = str(int((float(temp) * 9 / 5) + 32))
                except (ValueError, TypeError):
                    pass

            temp_label = Label(
                self.current_frame,
                text=f"{temp}{temp_symbol}",
                font=("Arial", 32, "bold"),
                bg=theme.get("background_color", "#F0F0F0"),
                fg=theme.get("text_color", "#333333"),
            )
            temp_label.pack(pady=10)

            condition_label = Label(
                self.current_frame,
                text=self.current_weather.get("condition", "N/A"),
                font=("Arial", 12),
                bg=theme.get("background_color", "#F0F0F0"),
                fg=theme.get("text_color", "#333333"),
            )
            condition_label.pack(pady=5)

            # Details
            details_frame = Frame(self.current_frame, bg=theme.get("background_color", "#F0F0F0"))
            details_frame.pack(pady=10)

            details = []
            if display_config.get("show_humidity", True):
                details.append(f"Humidity: {self.current_weather.get('humidity', 'N/A')}%")
            if display_config.get("show_wind", True):
                wind = self.current_weather.get("wind_speed", "N/A")
                direction = self.current_weather.get("wind_direction", "N/A")
                details.append(f"Wind: {wind} km/h {direction}")
            if display_config.get("show_pressure", True):
                details.append(f"Pressure: {self.current_weather.get('pressure', 'N/A')} mb")
            if display_config.get("show_visibility", True):
                details.append(f"Visibility: {self.current_weather.get('visibility', 'N/A')} km")

            for detail in details:
                detail_label = Label(
                    details_frame,
                    text=detail,
                    font=("Arial", 9),
                    bg=theme.get("background_color", "#F0F0F0"),
                    fg=theme.get("text_color", "#333333"),
                )
                detail_label.pack(anchor="w", pady=2)

        # Display forecast
        if display_config.get("show_forecast", True) and self.forecast:
            Label(
                self.forecast_frame,
                text="Forecast",
                font=("Arial", 12, "bold"),
                bg=theme.get("background_color", "#F0F0F0"),
                fg=theme.get("text_color", "#333333"),
            ).pack(pady=(10, 5))

            for day in self.forecast:
                forecast_item = Frame(
                    self.forecast_frame, bg=theme.get("background_color", "#F0F0F0")
                )
                forecast_item.pack(fill="x", pady=5)

                temp_unit = display_config.get("temperature_unit", "C")
                temp_symbol = "°C" if temp_unit == "C" else "°F"

                max_temp = day.get("max_temp", "N/A")
                min_temp = day.get("min_temp", "N/A")
                if temp_unit == "F":
                    try:
                        max_temp = str(int((float(max_temp) * 9 / 5) + 32))
                        min_temp = str(int((float(min_temp) * 9 / 5) + 32))
                    except (ValueError, TypeError):
                        pass

                forecast_text = (
                    f"{day.get('date', 'N/A')}: {day.get('condition', 'N/A')} - "
                    f"High: {max_temp}{temp_symbol}, Low: {min_temp}{temp_symbol}"
                )

                forecast_label = Label(
                    forecast_item,
                    text=forecast_text,
                    font=("Arial", 9),
                    bg=theme.get("background_color", "#F0F0F0"),
                    fg=theme.get("text_color", "#333333"),
                    justify="left",
                )
                forecast_label.pack(anchor="w")

        # Update status
        if self.current_weather:
            self.status_var.set(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

    def run(self) -> None:
        """Run the weather scraper application."""
        if Tk is None:
            logger.error("tkinter not available. Cannot run GUI.")
            return

        self._create_main_window()

        # Start auto-refresh if enabled
        if self.config.get("updates", {}).get("auto_refresh", True):
            self.running = True
            self.refresh_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
            self.refresh_thread.start()

        logger.info("Starting weather scraper application")
        self.root.mainloop()

        # Stop auto-refresh
        self.running = False
        logger.info("Weather scraper application closed")


def main() -> int:
    """Main entry point for weather scraper."""
    import argparse

    parser = argparse.ArgumentParser(description="Weather Scraper")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-l",
        "--location",
        help="City name to fetch weather for",
    )

    args = parser.parse_args()

    try:
        scraper = WeatherScraper(config_path=args.config)

        if args.location:
            scraper.fetch_weather(args.location)

        scraper.run()
        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
