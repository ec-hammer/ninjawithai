"""
Configuration settings for RFID Product System
"""

# Database Configuration
DB_PATH = "products.db"
DB_TIMEOUT = 5.0

# RFID Configuration
RFID_SCAN_INTERVAL = 1.0  # Scan once per second
RFID_DEBOUNCE_STABLE = 2.0  # Require 2 seconds stability to accept new tag
RFID_NO_INFO_TIMEOUT = 3.0  # Show "No Information" after 3 seconds if not found
RFID_SERIAL_PORT = "/dev/ttyUSB0"  # Change for your system
RFID_BAUD_RATE = 115200

# Display Configuration
DISPLAY_I2C_ADDRESS = 0x3C
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
DISPLAY_FIELD_DURATION = 5  # Show each field for 5 seconds
DISPLAY_SEARCH_MESSAGE = "Searching..."
DISPLAY_NO_INFO_MESSAGE = "No Information"

# Image Configuration
IMAGE_MAX_WIDTH = 128
IMAGE_MAX_HEIGHT = 32
IMAGE_STORAGE_PATH = "product_images/"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "rfid_system.log"