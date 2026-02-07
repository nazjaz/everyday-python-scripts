"""Stock Tracker - GUI application for tracking stock prices and gains.

This module provides a GUI application for scraping stock prices from financial
websites, displaying them in a dashboard, tracking price changes, and
calculating gains. Includes data persistence and comprehensive logging.
"""

import argparse
import json
import logging
import logging.handlers
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv
import yfinance as yf

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    tk = None
    ttk = None
    messagebox = None

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class StockDataManager:
    """Manages stock data storage and retrieval."""

    def __init__(self, data_file: Path) -> None:
        """Initialize StockDataManager.

        Args:
            data_file: Path to JSON data file.
        """
        self.data_file = data_file
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.stock_data: Dict[str, Dict] = {}
        self.load_data()

    def load_data(self) -> None:
        """Load stock data from file."""
        try:
            if self.data_file.exists():
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.stock_data = json.load(f)
                logger.info(
                    f"Loaded data for {len(self.stock_data)} stocks from {self.data_file}"
                )
            else:
                self.stock_data = {}
                logger.info("Data file not found, starting with empty data")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading data: {e}")
            self.stock_data = {}
            if messagebox:
                messagebox.showerror("Error", f"Failed to load stock data: {e}")

    def save_data(self) -> None:
        """Save stock data to file."""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.stock_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved data for {len(self.stock_data)} stocks to {self.data_file}")
        except IOError as e:
            logger.error(f"Error saving data: {e}")
            if messagebox:
                messagebox.showerror("Error", f"Failed to save stock data: {e}")

    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get stored stock information.

        Args:
            symbol: Stock symbol.

        Returns:
            Stock information dictionary or None if not found.
        """
        return self.stock_data.get(symbol.upper())

    def update_stock_info(
        self, symbol: str, current_price: float, previous_price: Optional[float] = None
    ) -> None:
        """Update stock information.

        Args:
            symbol: Stock symbol.
            current_price: Current stock price.
            previous_price: Previous price for comparison.
        """
        symbol = symbol.upper()
        if symbol not in self.stock_data:
            self.stock_data[symbol] = {
                "first_price": current_price,
                "last_price": current_price,
                "last_update": datetime.now().isoformat(),
            }
        else:
            if previous_price is None:
                previous_price = self.stock_data[symbol]["last_price"]
            self.stock_data[symbol]["last_price"] = current_price
            self.stock_data[symbol]["last_update"] = datetime.now().isoformat()

        self.save_data()


class StockPriceScraper:
    """Handles fetching stock prices from financial websites."""

    @staticmethod
    def get_stock_price(symbol: str) -> Optional[Dict[str, float]]:
        """Fetch current stock price and related data.

        Args:
            symbol: Stock symbol (e.g., 'AAPL').

        Returns:
            Dictionary with price data or None if fetch failed.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get current price
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")

            if current_price is None:
                # Try getting from history
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = float(hist["Close"].iloc[-1])
                else:
                    logger.warning(f"Could not fetch price for {symbol}")
                    return None

            # Get previous close
            previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")

            if previous_close is None:
                # Try getting from history
                hist = ticker.history(period="2d")
                if not hist.empty and len(hist) > 1:
                    previous_close = float(hist["Close"].iloc[-2])
                else:
                    previous_close = current_price

            return {
                "current_price": float(current_price),
                "previous_close": float(previous_close),
                "open": float(info.get("open", current_price)),
                "high": float(info.get("dayHigh", current_price)),
                "low": float(info.get("dayLow", current_price)),
            }

        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {e}")
            return None

    @staticmethod
    def get_stock_name(symbol: str) -> str:
        """Get stock company name.

        Args:
            symbol: Stock symbol.

        Returns:
            Company name or symbol if not found.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get("longName", symbol)
        except Exception:
            return symbol


class StockTrackerGUI:
    """Main GUI application for stock tracking."""

    def __init__(self, root: tk.Tk, config: Dict) -> None:
        """Initialize StockTrackerGUI.

        Args:
            root: Tkinter root window.
            config: Configuration dictionary.
        """
        self.root = root
        self.config = config
        self.data_manager = StockDataManager(Path(config["data_file"]))
        self.scraper = StockPriceScraper()
        self.stocks: List[str] = config.get("default_stocks", ["AAPL", "MSFT", "GOOGL"]).copy()
        self.update_thread = None
        self.running = False

        self.setup_window()
        self.create_widgets()
        self.update_dashboard()
        self.start_auto_refresh()

    def setup_window(self) -> None:
        """Configure main window properties."""
        self.root.title("Stock Price Tracker")
        window_size = self.config.get("window_size", "1000x700")
        self.root.geometry(window_size)

    def create_widgets(self) -> None:
        """Create and layout all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Add Stock Section
        add_frame = ttk.LabelFrame(main_frame, text="Add Stock", padding="10")
        add_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(add_frame, text="Symbol:").grid(row=0, column=0, padx=5, pady=5)
        self.symbol_var = tk.StringVar()
        symbol_entry = ttk.Entry(add_frame, textvariable=self.symbol_var, width=15)
        symbol_entry.grid(row=0, column=1, padx=5, pady=5)

        add_button = ttk.Button(
            add_frame, text="Add Stock", command=self.add_stock
        )
        add_button.grid(row=0, column=2, padx=5, pady=5)

        remove_button = ttk.Button(
            add_frame, text="Remove Stock", command=self.remove_stock
        )
        remove_button.grid(row=0, column=3, padx=5, pady=5)

        refresh_button = ttk.Button(
            add_frame, text="Refresh Now", command=self.update_dashboard
        )
        refresh_button.grid(row=0, column=4, padx=5, pady=5)

        # Dashboard Section
        dashboard_frame = ttk.LabelFrame(main_frame, text="Stock Dashboard", padding="10")
        dashboard_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Dashboard Treeview
        columns = ("Symbol", "Name", "Price", "Change", "Change %", "Gain", "Gain %", "Last Update")
        self.dashboard_tree = ttk.Treeview(
            dashboard_frame, columns=columns, show="headings", height=15
        )

        # Configure columns
        self.dashboard_tree.heading("Symbol", text="Symbol")
        self.dashboard_tree.heading("Name", text="Company Name")
        self.dashboard_tree.heading("Price", text="Current Price")
        self.dashboard_tree.heading("Change", text="Change")
        self.dashboard_tree.heading("Change %", text="Change %")
        self.dashboard_tree.heading("Gain", text="Gain")
        self.dashboard_tree.heading("Gain %", text="Gain %")
        self.dashboard_tree.heading("Last Update", text="Last Update")

        self.dashboard_tree.column("Symbol", width=80)
        self.dashboard_tree.column("Name", width=200)
        self.dashboard_tree.column("Price", width=100)
        self.dashboard_tree.column("Change", width=100)
        self.dashboard_tree.column("Change %", width=100)
        self.dashboard_tree.column("Gain", width=100)
        self.dashboard_tree.column("Gain %", width=100)
        self.dashboard_tree.column("Last Update", width=150)

        scrollbar = ttk.Scrollbar(
            dashboard_frame, orient=tk.VERTICAL, command=self.dashboard_tree.yview
        )
        self.dashboard_tree.configure(yscrollcommand=scrollbar.set)

        self.dashboard_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        dashboard_frame.columnconfigure(0, weight=1)
        dashboard_frame.rowconfigure(0, weight=1)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN
        )
        status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)

    def add_stock(self) -> None:
        """Handle add stock button click."""
        symbol = self.symbol_var.get().strip().upper()

        if not symbol:
            messagebox.showerror("Error", "Please enter a stock symbol")
            return

        if symbol in self.stocks:
            messagebox.showwarning("Warning", f"{symbol} is already being tracked")
            return

        # Verify stock exists
        price_data = self.scraper.get_stock_price(symbol)
        if price_data is None:
            messagebox.showerror("Error", f"Could not fetch data for {symbol}. Please check the symbol.")
            return

        self.stocks.append(symbol)
        self.symbol_var.set("")
        self.update_dashboard()
        messagebox.showinfo("Success", f"Added {symbol} to tracking list")

    def remove_stock(self) -> None:
        """Handle remove stock button click."""
        symbol = self.symbol_var.get().strip().upper()

        if not symbol:
            messagebox.showerror("Error", "Please enter a stock symbol")
            return

        if symbol not in self.stocks:
            messagebox.showwarning("Warning", f"{symbol} is not being tracked")
            return

        self.stocks.remove(symbol)
        self.symbol_var.set("")
        self.update_dashboard()
        messagebox.showinfo("Success", f"Removed {symbol} from tracking list")

    def calculate_gain(self, symbol: str, current_price: float) -> Tuple[float, float]:
        """Calculate gain from first tracked price.

        Args:
            symbol: Stock symbol.
            current_price: Current stock price.

        Returns:
            Tuple of (absolute_gain, percentage_gain).
        """
        stock_info = self.data_manager.get_stock_info(symbol)
        if stock_info and "first_price" in stock_info:
            first_price = stock_info["first_price"]
            absolute_gain = current_price - first_price
            percentage_gain = (absolute_gain / first_price) * 100 if first_price > 0 else 0
            return absolute_gain, percentage_gain
        return 0.0, 0.0

    def update_dashboard(self) -> None:
        """Update the stock dashboard with current prices."""
        # Clear existing items
        for item in self.dashboard_tree.get_children():
            self.dashboard_tree.delete(item)

        if not self.stocks:
            self.status_var.set("No stocks being tracked")
            return

        self.status_var.set(f"Updating {len(self.stocks)} stock(s)...")

        for symbol in self.stocks:
            try:
                # Fetch current price
                price_data = self.scraper.get_stock_price(symbol)
                if price_data is None:
                    self.dashboard_tree.insert(
                        "",
                        tk.END,
                        values=(
                            symbol,
                            "Error fetching data",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                        tags=("error",),
                    )
                    continue

                current_price = price_data["current_price"]
                previous_close = price_data["previous_close"]

                # Calculate change from previous close
                change = current_price - previous_close
                change_percent = (change / previous_close * 100) if previous_close > 0 else 0

                # Calculate gain from first tracked price
                absolute_gain, percentage_gain = self.calculate_gain(symbol, current_price)

                # Update stored data
                stock_info = self.data_manager.get_stock_info(symbol)
                previous_price = stock_info["last_price"] if stock_info else None
                self.data_manager.update_stock_info(symbol, current_price, previous_price)

                # Get company name
                company_name = self.scraper.get_stock_name(symbol)

                # Format values
                price_str = f"${current_price:.2f}"
                change_str = f"${change:+.2f}"
                change_percent_str = f"{change_percent:+.2f}%"
                gain_str = f"${absolute_gain:+.2f}"
                gain_percent_str = f"{percentage_gain:+.2f}%"

                # Determine tags for color coding
                tags = []
                if change_percent >= self.config.get("thresholds", {}).get("positive_change", 0.01) * 100:
                    tags.append("positive")
                elif change_percent <= self.config.get("thresholds", {}).get("negative_change", -0.01) * 100:
                    tags.append("negative")

                # Insert row
                self.dashboard_tree.insert(
                    "",
                    tk.END,
                    values=(
                        symbol,
                        company_name,
                        price_str,
                        change_str,
                        change_percent_str,
                        gain_str,
                        gain_percent_str,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                    tags=tags,
                )

            except Exception as e:
                logger.error(f"Error updating {symbol}: {e}")
                self.dashboard_tree.insert(
                    "",
                    tk.END,
                    values=(
                        symbol,
                        "Error",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                    tags=("error",),
                )

        # Configure tag colors
        self.dashboard_tree.tag_configure("positive", foreground="green")
        self.dashboard_tree.tag_configure("negative", foreground="red")
        self.dashboard_tree.tag_configure("error", foreground="gray")

        self.status_var.set(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def start_auto_refresh(self) -> None:
        """Start automatic dashboard refresh."""
        refresh_rate = self.config.get("refresh_rate", 5000)
        self.running = True

        def refresh_loop():
            while self.running:
                time.sleep(refresh_rate / 1000.0)
                if self.running:
                    self.root.after(0, self.update_dashboard)

        self.update_thread = threading.Thread(target=refresh_loop, daemon=True)
        self.update_thread.start()

    def stop_auto_refresh(self) -> None:
        """Stop automatic dashboard refresh."""
        self.running = False


def setup_logging(config: Dict) -> None:
    """Configure logging based on config file.

    Args:
        config: Configuration dictionary with logging settings.
    """
    log_config = config.get("logging", {})
    log_level = os.getenv("LOG_LEVEL", log_config.get("level", "INFO"))
    log_file = log_config.get("file", "logs/stock_tracker.log")
    max_bytes = log_config.get("max_bytes", 10485760)
    backup_count = log_config.get("backup_count", 5)
    log_format = log_config.get(
        "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)


def load_config(config_path: Optional[Path] = None) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config.yaml in project root.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is invalid.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Stock Price Tracker GUI Application")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        setup_logging(config)

        if tk is None:
            logger.error("tkinter is not available. Please install python3-tk")
            print("Error: tkinter is not available. Please install python3-tk")
            return

        root = tk.Tk()
        app = StockTrackerGUI(root, config)

        def on_closing():
            app.stop_auto_refresh()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
    except yaml.YAMLError as e:
        logger.error(f"Invalid configuration file: {e}")
        print(f"Error: Invalid configuration file: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
