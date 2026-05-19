"""
Display Module - Cheap yellow OLED display management
Shows product info, rotates through fields every 5 seconds
"""

import logging
import threading
import time
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class DisplayModule:
    """
    OLED display module for showing product information.
    - Rotates through product fields every 5 seconds
    - Shows product image, description, characteristics, etc.
    - Displays "Searching..." for unstable reads
    - Displays "No Information" if tag not found
    """

    def __init__(
        self,
        width=128,
        height=64,
        field_duration=5,
        i2c_address=0x3C,
        use_simulator=False,
    ):
        """
        Initialize display.

        Args:
            width: Display width in pixels
            height: Display height in pixels
            field_duration: Duration to show each field (seconds)
            i2c_address: I2C address of display
            use_simulator: Use text simulator if True (for testing)
        """
        self.width = width
        self.height = height
        self.field_duration = field_duration
        self.i2c_address = i2c_address
        self.use_simulator = use_simulator

        self.device = None
        self.current_product = None
        self.current_field_index = 0
        self.field_change_time = 0

        self.is_running = False
        self.display_thread = None

        self.init_display()

    def init_display(self):
        """Initialize the display device."""
        try:
            if not self.use_simulator:
                import board
                import busio
                from luma.oled.device import sh1106

                i2c = busio.I2C(board.SCL, board.SDA)
                self.device = sh1106(i2c, address=self.i2c_address)
                logger.info(f"Display initialized at address {hex(self.i2c_address)}")
            else:
                logger.info("Display simulator mode enabled")

        except Exception as e:
            logger.error(f"Failed to initialize display: {e}")
            logger.warning("Using text-based display simulator")
            self.use_simulator = True

    def start(self):
        """Start display update loop."""
        if not self.is_running:
            self.is_running = True
            self.display_thread = threading.Thread(
                target=self._update_loop, daemon=True
            )
            self.display_thread.start()
            logger.info("Display started")

    def stop(self):
        """Stop display update loop."""
        self.is_running = False
        if self.display_thread:
            self.display_thread.join(timeout=5)
        logger.info("Display stopped")

    def _update_loop(self):
        """Main display update loop."""
        while self.is_running:
            try:
                current_time = time.time()

                if (
                    self.current_product
                    and current_time - self.field_change_time >= self.field_duration
                ):
                    self._next_field()
                    self.field_change_time = current_time

                time.sleep(0.5)  # Update display every 500ms

            except Exception as e:
                logger.error(f"Error in display update loop: {e}")
                time.sleep(0.5)

    def show_product(self, product):
        """
        Display product information.

        Args:
            product: Dictionary with product data
        """
        self.current_product = product
        self.current_field_index = 0
        self.field_change_time = time.time()
        self._render_current_field()
        logger.info(f"Displaying product: {product.get('product_name', 'Unknown')}")

    def show_searching(self):
        """Display 'Searching...' message."""
        self._render_text("Searching...")
        logger.debug("Displaying: Searching...")

    def show_no_information(self):
        """Display 'No Information' message."""
        self._render_text("No Information")
        logger.debug("Displaying: No Information")

    def show_idle(self):
        """Display idle state."""
        self._render_text("Ready", "Place tag on reader")
        logger.debug("Displaying: Idle")

    def _next_field(self):
        """Move to next product field."""
        if not self.current_product:
            return

        # Define field sequence
        fields = [
            ("product_name", "Name"),
            ("product_description", "Description"),
            ("product_characteristics", "Characteristics"),
            ("product_type", "Type"),
            ("option_field_1", "Option 1"),
            ("option_field_2", "Option 2"),
            ("image_path", "Image"),
        ]

        self.current_field_index = (self.current_field_index + 1) % len(fields)
        self._render_current_field()

    def _render_current_field(self):
        """Render the current product field."""
        if not self.current_product:
            return

        fields = [
            ("product_name", "Name"),
            ("product_description", "Description"),
            ("product_characteristics", "Characteristics"),
            ("product_type", "Type"),
            ("option_field_1", "Option 1"),
            ("option_field_2", "Option 2"),
            ("image_path", "Image"),
        ]

        field_key, field_label = fields[self.current_field_index]
        field_value = self.current_product.get(field_key, "")

        if field_key == "image_path" and field_value:
            self._render_image(field_value)
        else:
            self._render_text(field_label, str(field_value) if field_value else "(empty)")

    def _render_text(self, title, content=""):
        """Render text on display."""
        try:
            image = Image.new("1", (self.width, self.height), color=0)
            draw = ImageDraw.Draw(image)

            # Try to load a font, fall back to default
            try:
                font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
                font_content = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10
                )
            except:
                font_title = ImageFont.load_default()
                font_content = ImageFont.load_default()

            # Draw title
            draw.text((2, 2), title, fill=1, font=font_title)

            # Draw content with word wrapping
            if content:
                y_offset = 20
                words = content.split()
                line = ""

                for word in words:
                    test_line = f"{line} {word}".strip()
                    if draw.textbbox((0, 0), test_line, font=font_content)[2] < self.width - 4:
                        line = test_line
                    else:
                        if line:
                            draw.text((4, y_offset), line, fill=1, font=font_content)
                            y_offset += 12
                        line = word

                if line:
                    draw.text((4, y_offset), line, fill=1, font=font_content)

            if not self.use_simulator:
                self.device.display(image)
            else:
                self._print_simulator(title, content)

        except Exception as e:
            logger.error(f"Error rendering text: {e}")

    def _render_image(self, image_path):
        """Render image on display."""
        try:
            img = Image.open(image_path)
            img.thumbnail((self.width, self.height), Image.Resampling.LANCZOS)

            # Create new image and paste
            display_img = Image.new("1", (self.width, self.height), color=0)
            offset = (
                (self.width - img.width) // 2,
                (self.height - img.height) // 2,
            )
            display_img.paste(img, offset)

            if not self.use_simulator:
                self.device.display(display_img)
            else:
                logger.info(f"Would display image: {image_path}")

        except Exception as e:
            logger.error(f"Error rendering image: {e}")
            self._render_text("Image Error", f"Could not load: {image_path}")

    def _print_simulator(self, title, content):
        """Print to console in simulator mode."""
        print(f"\n{'='*40}")
        print(f"[DISPLAY] {title}")
        if content:
            print(f"          {content}")
        print(f"{'='*40}\n")