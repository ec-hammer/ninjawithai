"""
RFID Module - NFC tag reading/writing with debouncing
Supports PN532 via UART or I2C
"""

import logging
import threading
import time
from collections import deque
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class RFIDReader(ABC):
    """Abstract base class for RFID readers."""

    @abstractmethod
    def read_tag(self):
        """Read RFID tag and return code."""
        pass

    @abstractmethod
    def write_tag(self, code):
        """Write code to RFID tag."""
        pass

    @abstractmethod
    def is_tag_present(self):
        """Check if tag is present."""
        pass


class PN532Reader(RFIDReader):
    """PN532 NFC Reader/Writer implementation."""

    def __init__(self, interface_type="uart", **kwargs):
        """
        Initialize PN532 reader.
        interface_type: 'uart' or 'i2c'
        """
        self.interface_type = interface_type
        self.reader = None
        self.init_reader(**kwargs)

    def init_reader(self, **kwargs):
        """Initialize the PN532 reader based on interface type."""
        try:
            if self.interface_type == "uart":
                import serial
                from adafruit_pn532.i2c import Adafruit_PN532_I2C

                port = kwargs.get("port", "/dev/ttyUSB0")
                baudrate = kwargs.get("baudrate", 115200)
                self.serial_conn = serial.Serial(port, baudrate, timeout=1)
                logger.info(f"PN532 UART initialized on {port}")

            elif self.interface_type == "i2c":
                import board
                import busio
                from adafruit_pn532.i2c import Adafruit_PN532_I2C

                i2c = busio.I2C(board.SCL, board.SDA)
                self.reader = Adafruit_PN532_I2C(i2c)
                self.reader.begin()
                logger.info("PN532 I2C initialized")

        except Exception as e:
            logger.error(f"Failed to initialize PN532 reader: {e}")
            raise

    def read_tag(self):
        """Read RFID tag UID."""
        try:
            if self.interface_type == "i2c":
                uid = self.reader.read_passive_target()
                if uid:
                    return uid.hex().upper()
            return None
        except Exception as e:
            logger.error(f"Error reading tag: {e}")
            return None

    def write_tag(self, code):
        """Write code to RFID tag."""
        try:
            if self.interface_type == "i2c":
                # Write NDEF message with code
                from adafruit_pn532.ndef import NdefMessage

                message = NdefMessage()
                message.add_text_record(code)

                success = self.reader.write_ndef_message(message)
                logger.info(f"Tag write {'successful' if success else 'failed'}")
                return success
            return False
        except Exception as e:
            logger.error(f"Error writing tag: {e}")
            return False

    def is_tag_present(self):
        """Check if tag is present (passive mode)."""
        try:
            return self.read_tag() is not None
        except Exception:
            return False


class RFIDModule:
    """
    RFID scanning module with debouncing logic.
    - Scans once per second
    - Requires 2 seconds stability for new tag
    - Shows "No Information" after 3 seconds if not found
    - Shows "Searching" for unstable reads
    """

    def __init__(
        self,
        reader,
        scan_interval=1.0,
        debounce_stable=2.0,
        no_info_timeout=3.0,
        callback=None,
    ):
        """
        Initialize RFID module.

        Args:
            reader: RFIDReader instance
            scan_interval: Scan interval in seconds
            debounce_stable: Time required for stable read (seconds)
            no_info_timeout: Time before showing "No Information" (seconds)
            callback: Callback function for tag changes
        """
        self.reader = reader
        self.scan_interval = scan_interval
        self.debounce_stable = debounce_stable
        self.no_info_timeout = no_info_timeout
        self.callback = callback

        self.current_tag = None
        self.previous_tag = None
        self.tag_stable_time = 0
        self.tag_detection_time = 0

        self.is_running = False
        self.scan_thread = None

    def start(self):
        """Start RFID scanning in background thread."""
        if not self.is_running:
            self.is_running = True
            self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
            self.scan_thread.start()
            logger.info("RFID scanning started")

    def stop(self):
        """Stop RFID scanning."""
        self.is_running = False
        if self.scan_thread:
            self.scan_thread.join(timeout=5)
        logger.info("RFID scanning stopped")

    def _scan_loop(self):
        """Main scanning loop."""
        while self.is_running:
            try:
                tag = self.reader.read_tag()
                self._process_tag(tag)
                time.sleep(self.scan_interval)

            except Exception as e:
                logger.error(f"Error in scan loop: {e}")
                time.sleep(self.scan_interval)

    def _process_tag(self, tag):
        """Process detected tag with debouncing logic."""
        current_time = time.time()

        if tag is None:
            # No tag detected
            self.current_tag = None
            self.tag_stable_time = 0
            return

        if tag == self.current_tag:
            # Same tag detected - check if stable now
            if self.tag_stable_time == 0:
                self.tag_stable_time = current_time

            elapsed = current_time - self.tag_stable_time

            if elapsed >= self.debounce_stable and self.previous_tag != tag:
                # Tag is stable and different - trigger callback
                self.previous_tag = tag
                if self.callback:
                    self.callback("new_tag", tag)
                logger.info(f"New stable tag detected: {tag}")

        else:
            # Different tag detected
            self.current_tag = tag
            self.tag_stable_time = current_time
            self.tag_detection_time = current_time

            if self.callback:
                self.callback("searching", tag)

    def get_current_tag(self):
        """Get currently detected tag."""
        return self.current_tag

    def get_tag_state(self):
        """Get current scanning state."""
        if self.current_tag is None:
            return "idle", None

        current_time = time.time()
        elapsed = current_time - self.tag_stable_time if self.tag_stable_time else 0

        if elapsed < self.debounce_stable:
            return "searching", self.current_tag

        if elapsed > self.no_info_timeout and self.previous_tag != self.current_tag:
            return "no_info", self.current_tag

        return "found", self.current_tag

    def write_tag(self, code):
        """Write code to tag."""
        try:
            success = self.reader.write_tag(code)
            logger.info(f"Tag write {'successful' if success else 'failed'}: {code}")
            return success
        except Exception as e:
            logger.error(f"Error writing tag: {e}")
            return False