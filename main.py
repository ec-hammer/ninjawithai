"""
Main application - Integrates all modules
RFID Product Display System
"""

import logging
import sys
import signal
import time
from database_module import DatabaseModule
from rfid_module import RFIDModule, PN532Reader
from display_module import DisplayModule

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("rfid_system.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


class RFIDProductSystem:
    """Main RFID Product Display System."""

    def __init__(self, use_simulator=False):
        """
        Initialize the system.

        Args:
            use_simulator: Use display simulator for testing without hardware
        """
        logger.info("Initializing RFID Product System...")

        self.use_simulator = use_simulator
        self.db = DatabaseModule()
        self.display = DisplayModule(use_simulator=use_simulator)

        # Initialize RFID reader
        try:
            if use_simulator:
                logger.info("Using RFID simulator mode")
                self.rfid_reader = None
            else:
                self.rfid_reader = PN532Reader(interface_type="i2c")
                self.rfid_module = RFIDModule(
                    self.rfid_reader,
                    scan_interval=1.0,
                    debounce_stable=2.0,
                    no_info_timeout=3.0,
                    callback=self._rfid_callback,
                )
        except Exception as e:
            logger.error(f"Failed to initialize RFID reader: {e}")
            logger.warning("Running in display-only mode")
            self.rfid_reader = None
            self.rfid_module = None

        self.is_running = False

    def _rfid_callback(self, event_type, tag_data):
        """
        Callback for RFID events.

        Args:
            event_type: 'new_tag', 'searching', 'no_info'
            tag_data: The RFID tag data
        """
        logger.info(f"RFID Event: {event_type} - {tag_data}")

        if event_type == "searching":
            self.display.show_searching()

        elif event_type == "new_tag":
            product = self.db.get_product_by_rfid(tag_data)
            if product:
                self.display.show_product(product)
                logger.info(f"Displaying product: {product['product_name']}")
            else:
                self.display.show_no_information()
                logger.warning(f"No product found for RFID: {tag_data}")

    def start(self):
        """Start the system."""
        logger.info("Starting RFID Product System")
        self.is_running = True

        self.display.start()

        if self.rfid_module:
            self.rfid_module.start()
        else:
            self.display.show_idle()

        logger.info("System started successfully")

    def stop(self):
        """Stop the system."""
        logger.info("Stopping RFID Product System")
        self.is_running = False

        if self.rfid_module:
            self.rfid_module.stop()

        self.display.stop()

        logger.info("System stopped")

    def run(self):
        """Run the main system loop."""
        self.start()

        try:
            while self.is_running:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.stop()

    def demo_mode(self):
        """Run in demo mode without RFID hardware."""
        logger.info("Running in demo mode")
        self.start()

        # Create sample products if none exist
        products = self.db.get_all_products()
        if not products:
            logger.info("Creating sample products for demo...")
            self.db.create_product(
                rfid_code="DEMO001",
                product_name="Sample Product 1",
                product_description="This is a sample product for demo",
                product_type="Demo",
                product_characteristics="High quality, durable",
            )
            self.db.create_product(
                rfid_code="DEMO002",
                product_name="Sample Product 2",
                product_description="Another sample product",
                product_type="Demo",
                product_characteristics="Lightweight, portable",
            )

        try:
            while self.is_running:
                print("\nDemo Mode - Available commands:")
                print("  1 - Show product DEMO001")
                print("  2 - Show product DEMO002")
                print("  3 - Show searching state")
                print("  4 - Show no information")
                print("  5 - Show idle")
                print("  q - Quit")

                choice = input("\nCommand: ").lower().strip()

                if choice == "1":
                    product = self.db.get_product_by_rfid("DEMO001")
                    if product:
                        self.display.show_product(product)
                elif choice == "2":
                    product = self.db.get_product_by_rfid("DEMO002")
                    if product:
                        self.display.show_product(product)
                elif choice == "3":
                    self.display.show_searching()
                elif choice == "4":
                    self.display.show_no_information()
                elif choice == "5":
                    self.display.show_idle()
                elif choice == "q":
                    break

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.stop()


def signal_handler(sig, frame):
    """Handle system signals."""
    logger.info("Received signal, shutting down...")
    sys.exit(0)


def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    import argparse

    parser = argparse.ArgumentParser(description="RFID Product Display System")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode without RFID hardware",
    )
    parser.add_argument(
        "--simulator",
        action="store_true",
        help="Use display simulator (text-based)",
    )

    args = parser.parse_args()

    system = RFIDProductSystem(use_simulator=args.simulator)

    if args.demo:
        system.demo_mode()
    else:
        system.run()


if __name__ == "__main__":
    main()