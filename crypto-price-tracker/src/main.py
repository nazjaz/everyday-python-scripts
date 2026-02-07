"""Crypto Price Tracker - Scrape cryptocurrency prices and track portfolio.

This module provides a GUI application to scrape cryptocurrency prices from
public APIs, display them in a simple GUI with price alerts and portfolio tracking.
"""

import json
import logging
import logging.handlers
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import (
    END,
    Button,
    Entry,
    Frame,
    Label,
    Listbox,
    Menu,
    Scrollbar,
    StringVar,
    Tk,
    messagebox,
    ttk,
)
from typing import Any, Dict, List, Optional

import requests
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class CryptoPriceTracker:
    """GUI application for tracking cryptocurrency prices."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize CryptoPriceTracker with configuration.

        Args:
            config_path: Path to configuration YAML file.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.data_directory = self._get_data_directory()
        self.portfolio: Dict[str, Dict[str, Any]] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.prices: Dict[str, float] = {}
        self.update_thread: Optional[threading.Thread] = None
        self.running = False

        # Initialize GUI
        self.root = Tk()
        self._setup_gui()
        self._load_data()
        self._start_price_updates()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.
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
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {
                "api": {"base_url": "https://api.coingecko.com/api/v3", "timeout": 10},
                "app": {"title": "Crypto Price Tracker", "window_size": "800x600"},
                "update": {"interval_seconds": 60, "default_coins": ["bitcoin", "ethereum"]},
                "data": {"directory": "data"},
                "logging": {"level": "INFO", "file": "logs/crypto_tracker.log"},
            }

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables
        if os.getenv("API_KEY"):
            config["api"]["key"] = os.getenv("API_KEY")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/crypto_tracker.log")

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
            maxBytes=10485760,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        logger.info("Logging configured successfully")

    def _get_data_directory(self) -> Path:
        """Get data directory path.

        Returns:
            Path to data directory.
        """
        data_dir = self.config.get("data", {}).get("directory", "data")
        data_path = Path(data_dir)

        if not data_path.is_absolute():
            project_root = Path(__file__).parent.parent
            data_path = project_root / data_dir

        data_path.mkdir(parents=True, exist_ok=True)
        return data_path

    def _fetch_price(self, coin_id: str) -> Optional[float]:
        """Fetch cryptocurrency price from API.

        Args:
            coin_id: Coin identifier (e.g., 'bitcoin', 'ethereum').

        Returns:
            Current price in USD or None if fetch fails.
        """
        api_config = self.config.get("api", {})
        base_url = api_config.get("base_url", "https://api.coingecko.com/api/v3")
        timeout = api_config.get("timeout", 10)

        try:
            url = f"{base_url}/simple/price"
            params = {"ids": coin_id, "vs_currencies": "usd"}

            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()

            data = response.json()
            if coin_id in data and "usd" in data[coin_id]:
                price = data[coin_id]["usd"]
                logger.debug(f"Fetched price for {coin_id}: ${price}")
                return price

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching price for {coin_id}: {e}")
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing price data for {coin_id}: {e}")

        return None

    def _fetch_prices(self, coin_ids: List[str]) -> Dict[str, float]:
        """Fetch prices for multiple coins.

        Args:
            coin_ids: List of coin identifiers.

        Returns:
            Dictionary mapping coin IDs to prices.
        """
        api_config = self.config.get("api", {})
        base_url = api_config.get("base_url", "https://api.coingecko.com/api/v3")
        timeout = api_config.get("timeout", 10)

        prices = {}

        try:
            url = f"{base_url}/simple/price"
            ids_str = ",".join(coin_ids)
            params = {"ids": ids_str, "vs_currencies": "usd"}

            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()

            data = response.json()
            for coin_id in coin_ids:
                if coin_id in data and "usd" in data[coin_id]:
                    prices[coin_id] = data[coin_id]["usd"]

            logger.debug(f"Fetched prices for {len(prices)} coin(s)")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching prices: {e}")
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing price data: {e}")

        return prices

    def _update_prices(self) -> None:
        """Update prices for all tracked coins."""
        coin_ids = list(self.portfolio.keys())
        if not coin_ids:
            coin_ids = self.config.get("update", {}).get("default_coins", [])

        prices = self._fetch_prices(coin_ids)
        self.prices.update(prices)

        # Check alerts
        self._check_alerts()

        # Update GUI
        self.root.after(0, self._refresh_price_display)

    def _check_alerts(self) -> None:
        """Check if any price alerts should be triggered."""
        for alert in self.alerts:
            coin_id = alert.get("coin_id")
            target_price = alert.get("target_price")
            condition = alert.get("condition", "above")
            triggered = alert.get("triggered", False)

            if triggered or coin_id not in self.prices:
                continue

            current_price = self.prices[coin_id]
            should_trigger = False

            if condition == "above" and current_price >= target_price:
                should_trigger = True
            elif condition == "below" and current_price <= target_price:
                should_trigger = True

            if should_trigger:
                alert["triggered"] = True
                alert["triggered_at"] = datetime.now().isoformat()
                self.root.after(0, lambda: self._show_alert(alert))

    def _show_alert(self, alert: Dict[str, Any]) -> None:
        """Show price alert notification.

        Args:
            alert: Alert dictionary.
        """
        coin_id = alert.get("coin_id", "Unknown")
        target_price = alert.get("target_price", 0)
        condition = alert.get("condition", "above")
        current_price = self.prices.get(coin_id, 0)

        message = (
            f"Price Alert: {coin_id.upper()}\n\n"
            f"Price is now ${current_price:,.2f}\n"
            f"Target: ${target_price:,.2f} ({condition})"
        )

        messagebox.showinfo("Price Alert", message)
        self._save_data()

    def _setup_gui(self) -> None:
        """Set up the GUI interface."""
        app_title = self.config.get("app", {}).get("title", "Crypto Price Tracker")
        self.root.title(app_title)

        window_size = self.config.get("app", {}).get("window_size", "800x600")
        self.root.geometry(window_size)

        # Create menu bar
        self._create_menu_bar()

        # Main container
        main_frame = Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Left panel - Portfolio
        left_panel = Frame(main_frame, width=300)
        left_panel.pack(side="left", fill="both", padx=(0, 5))

        Label(left_panel, text="Portfolio", font=("Arial", 12, "bold")).pack(anchor="w")

        # Portfolio list
        portfolio_frame = Frame(left_panel)
        portfolio_frame.pack(fill="both", expand=True)

        scrollbar_portfolio = Scrollbar(portfolio_frame)
        scrollbar_portfolio.pack(side="right", fill="y")

        self.portfolio_listbox = Listbox(
            portfolio_frame, yscrollcommand=scrollbar_portfolio.set
        )
        self.portfolio_listbox.pack(side="left", fill="both", expand=True)
        scrollbar_portfolio.config(command=self.portfolio_listbox.yview)

        # Add coin frame
        add_frame = Frame(left_panel)
        add_frame.pack(fill="x", pady=(5, 0))

        Label(add_frame, text="Coin ID:").pack(side="left")
        self.coin_id_entry = Entry(add_frame, width=15)
        self.coin_id_entry.pack(side="left", padx=(5, 0))

        Label(add_frame, text="Amount:").pack(side="left", padx=(10, 0))
        self.amount_entry = Entry(add_frame, width=10)
        self.amount_entry.pack(side="left", padx=(5, 0))

        Button(add_frame, text="Add", command=self._add_to_portfolio).pack(
            side="left", padx=(5, 0)
        )

        Button(left_panel, text="Remove Selected", command=self._remove_from_portfolio).pack(
            fill="x", pady=(5, 0)
        )

        # Right panel - Prices and Alerts
        right_panel = Frame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True)

        # Prices display
        prices_frame = Frame(right_panel)
        prices_frame.pack(fill="both", expand=True)

        Label(prices_frame, text="Current Prices", font=("Arial", 12, "bold")).pack(anchor="w")

        self.prices_text = Label(
            prices_frame, text="Loading...", justify="left", anchor="nw", font=("Courier", 10)
        )
        self.prices_text.pack(fill="both", expand=True)

        # Alerts frame
        alerts_frame = Frame(right_panel)
        alerts_frame.pack(fill="x", pady=(5, 0))

        Label(alerts_frame, text="Price Alerts", font=("Arial", 12, "bold")).pack(anchor="w")

        # Add alert frame
        alert_add_frame = Frame(alerts_frame)
        alert_add_frame.pack(fill="x", pady=(5, 0))

        Label(alert_add_frame, text="Coin:").pack(side="left")
        self.alert_coin_entry = Entry(alert_add_frame, width=15)
        self.alert_coin_entry.pack(side="left", padx=(5, 0))

        Label(alert_add_frame, text="Price:").pack(side="left", padx=(10, 0))
        self.alert_price_entry = Entry(alert_add_frame, width=10)
        self.alert_price_entry.pack(side="left", padx=(5, 0))

        Label(alert_add_frame, text="Condition:").pack(side="left", padx=(10, 0))
        self.alert_condition = StringVar(value="above")
        ttk.Radiobutton(
            alert_add_frame, text="Above", variable=self.alert_condition, value="above"
        ).pack(side="left", padx=(5, 0))
        ttk.Radiobutton(
            alert_add_frame, text="Below", variable=self.alert_condition, value="below"
        ).pack(side="left", padx=(5, 0))

        Button(alert_add_frame, text="Add Alert", command=self._add_alert).pack(
            side="left", padx=(10, 0)
        )

        # Alerts list
        alerts_list_frame = Frame(alerts_frame)
        alerts_list_frame.pack(fill="both", expand=True, pady=(5, 0))

        scrollbar_alerts = Scrollbar(alerts_list_frame)
        scrollbar_alerts.pack(side="right", fill="y")

        self.alerts_listbox = Listbox(
            alerts_list_frame, yscrollcommand=scrollbar_alerts.set, height=5
        )
        self.alerts_listbox.pack(side="left", fill="both", expand=True)
        scrollbar_alerts.config(command=self.alerts_listbox.yview)

        Button(alerts_frame, text="Remove Alert", command=self._remove_alert).pack(
            fill="x", pady=(5, 0)
        )

        # Status bar
        self.status_var = StringVar(value="Ready")
        status_bar = Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

    def _create_menu_bar(self) -> None:
        """Create menu bar."""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh Prices", command=self._manual_update)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _load_data(self) -> None:
        """Load portfolio and alerts from data files."""
        portfolio_file = self.data_directory / "portfolio.json"
        alerts_file = self.data_directory / "alerts.json"

        # Load portfolio
        if portfolio_file.exists():
            try:
                with open(portfolio_file, "r", encoding="utf-8") as f:
                    self.portfolio = json.load(f)
                logger.info(f"Loaded {len(self.portfolio)} coin(s) from portfolio")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading portfolio: {e}")
                self.portfolio = {}
        else:
            self.portfolio = {}

        # Load alerts
        if alerts_file.exists():
            try:
                with open(alerts_file, "r", encoding="utf-8") as f:
                    self.alerts = json.load(f)
                logger.info(f"Loaded {len(self.alerts)} alert(s)")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading alerts: {e}")
                self.alerts = []
        else:
            self.alerts = []

        self._refresh_portfolio_display()
        self._refresh_alerts_display()

    def _save_data(self) -> None:
        """Save portfolio and alerts to data files."""
        portfolio_file = self.data_directory / "portfolio.json"
        alerts_file = self.data_directory / "alerts.json"

        try:
            with open(portfolio_file, "w", encoding="utf-8") as f:
                json.dump(self.portfolio, f, indent=2, ensure_ascii=False)
            logger.debug("Saved portfolio")

            with open(alerts_file, "w", encoding="utf-8") as f:
                json.dump(self.alerts, f, indent=2, ensure_ascii=False)
            logger.debug("Saved alerts")

        except IOError as e:
            logger.error(f"Error saving data: {e}")

    def _refresh_portfolio_display(self) -> None:
        """Refresh portfolio list display."""
        self.portfolio_listbox.delete(0, END)

        for coin_id, data in self.portfolio.items():
            amount = data.get("amount", 0)
            price = self.prices.get(coin_id, 0)
            value = amount * price

            display = f"{coin_id.upper():15s} {amount:>10.4f} @ ${price:>10,.2f} = ${value:>12,.2f}"
            self.portfolio_listbox.insert(END, display)

    def _refresh_price_display(self) -> None:
        """Refresh price display."""
        if not self.prices:
            self.prices_text.config(text="No prices available")
            return

        lines = []
        total_value = 0

        for coin_id, data in self.portfolio.items():
            amount = data.get("amount", 0)
            price = self.prices.get(coin_id, 0)
            value = amount * price
            total_value += value

            lines.append(
                f"{coin_id.upper():15s} ${price:>12,.2f}  "
                f"Amount: {amount:>10.4f}  Value: ${value:>12,.2f}"
            )

        # Add other tracked coins
        tracked_coins = set(self.portfolio.keys())
        for coin_id, price in self.prices.items():
            if coin_id not in tracked_coins:
                lines.append(f"{coin_id.upper():15s} ${price:>12,.2f}")

        if total_value > 0:
            lines.append("")
            lines.append(f"Total Portfolio Value: ${total_value:,.2f}")

        self.prices_text.config(text="\n".join(lines))
        self._refresh_portfolio_display()

    def _refresh_alerts_display(self) -> None:
        """Refresh alerts list display."""
        self.alerts_listbox.delete(0, END)

        for alert in self.alerts:
            coin_id = alert.get("coin_id", "Unknown")
            target_price = alert.get("target_price", 0)
            condition = alert.get("condition", "above")
            triggered = alert.get("triggered", False)

            status = "[TRIGGERED]" if triggered else "[ACTIVE]"
            display = f"{status} {coin_id.upper()} ${target_price:,.2f} ({condition})"
            self.alerts_listbox.insert(END, display)

    def _add_to_portfolio(self) -> None:
        """Add coin to portfolio."""
        coin_id = self.coin_id_entry.get().strip().lower()
        amount_str = self.amount_entry.get().strip()

        if not coin_id:
            messagebox.showwarning("Warning", "Please enter a coin ID.")
            return

        try:
            amount = float(amount_str)
            if amount < 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount.")
            return

        self.portfolio[coin_id] = {"amount": amount, "added_at": datetime.now().isoformat()}
        self._save_data()
        self._refresh_portfolio_display()
        self.coin_id_entry.delete(0, END)
        self.amount_entry.delete(0, END)

        # Fetch price for new coin
        price = self._fetch_price(coin_id)
        if price:
            self.prices[coin_id] = price
            self._refresh_price_display()

    def _remove_from_portfolio(self) -> None:
        """Remove selected coin from portfolio."""
        selection = self.portfolio_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a coin to remove.")
            return

        index = selection[0]
        coin_ids = list(self.portfolio.keys())
        if index < len(coin_ids):
            coin_id = coin_ids[index]
            del self.portfolio[coin_id]
            self._save_data()
            self._refresh_portfolio_display()
            self._refresh_price_display()

    def _add_alert(self) -> None:
        """Add price alert."""
        coin_id = self.alert_coin_entry.get().strip().lower()
        price_str = self.alert_price_entry.get().strip()
        condition = self.alert_condition.get()

        if not coin_id:
            messagebox.showwarning("Warning", "Please enter a coin ID.")
            return

        try:
            target_price = float(price_str)
            if target_price < 0:
                raise ValueError("Price must be positive")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid price.")
            return

        alert = {
            "coin_id": coin_id,
            "target_price": target_price,
            "condition": condition,
            "triggered": False,
            "created_at": datetime.now().isoformat(),
        }

        self.alerts.append(alert)
        self._save_data()
        self._refresh_alerts_display()
        self.alert_coin_entry.delete(0, END)
        self.alert_price_entry.delete(0, END)

    def _remove_alert(self) -> None:
        """Remove selected alert."""
        selection = self.alerts_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an alert to remove.")
            return

        index = selection[0]
        if index < len(self.alerts):
            del self.alerts[index]
            self._save_data()
            self._refresh_alerts_display()

    def _manual_update(self) -> None:
        """Manually trigger price update."""
        self.status_var.set("Updating prices...")
        self._update_prices()
        self.status_var.set("Prices updated")

    def _start_price_updates(self) -> None:
        """Start automatic price updates."""
        interval = self.config.get("update", {}).get("interval_seconds", 60)
        self.running = True

        def update_loop():
            while self.running:
                try:
                    self._update_prices()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Error in update loop: {e}")
                    time.sleep(interval)

        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()

        # Initial update
        self._update_prices()

    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "Crypto Price Tracker\n\n"
            "Track cryptocurrency prices, manage your portfolio, "
            "and set price alerts.\n\n"
            "Uses CoinGecko API for price data.\n\n"
            "Version 1.0",
        )

    def run(self) -> None:
        """Run the application."""
        logger.info("Starting Crypto Price Tracker application")

        def on_closing():
            self.running = False
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()


def main() -> int:
    """Main entry point for crypto price tracker application."""
    import argparse

    parser = argparse.ArgumentParser(description="Cryptocurrency price tracker with GUI")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    try:
        app = CryptoPriceTracker(config_path=args.config)
        app.run()
        return 0

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
