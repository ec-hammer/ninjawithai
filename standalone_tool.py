"""
Standalone tool for creating and managing product records
- Create new product records
- Upload images
- Generate unique RFID codes
- Write RFID codes to new tags
"""

import os
import sys
import logging
from pathlib import Path
from database_module import DatabaseModule
from rfid_module import PN532Reader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StandaloneTool:
    """Standalone product management tool."""

    def __init__(self, db_path="products.db"):
        """Initialize the standalone tool."""
        self.db = DatabaseModule(db_path)
        self.rfid_reader = None
        try:
            self.rfid_reader = PN532Reader(interface_type="i2c")
        except Exception as e:
            logger.warning(f"RFID reader not available: {e}")

        # Create image storage directory
        self.image_dir = Path("product_images")
        self.image_dir.mkdir(exist_ok=True)

    def interactive_create_product(self):
        """Interactive mode to create a new product."""
        print("\n" + "="*50)
        print("CREATE NEW PRODUCT RECORD")
        print("="*50)

        # Generate unique RFID code
        rfid_code = self.db.generate_unique_rfid_code()
        print(f"\nGenerated RFID Code: {rfid_code}")
        print("(This code will be written to the RFID tag)")

        # Get product information
        product_name = input("\nProduct Name: ").strip()
        if not product_name:
            print("Error: Product name is required")
            return False

        product_description = input("Product Description: ").strip()
        product_type = input("Product Type/Category: ").strip()
        product_characteristics = input("Product Characteristics: ").strip()
        option_field_1 = input("Option Field 1 (optional): ").strip()
        option_field_2 = input("Option Field 2 (optional): ").strip()

        # Handle image upload
        image_path = ""
        upload_image = input("\nUpload product image? (y/n): ").lower().strip()
        if upload_image == "y":
            image_path = self._upload_image(rfid_code)

        # Create product record
        try:
            product_id = self.db.create_product(
                rfid_code=rfid_code,
                product_name=product_name,
                product_description=product_description,
                product_type=product_type,
                product_characteristics=product_characteristics,
                image_path=image_path,
                option_field_1=option_field_1,
                option_field_2=option_field_2,
            )

            print(f"\n✓ Product created successfully (ID: {product_id})")

            # Offer to write to RFID tag
            write_tag = input("\nWrite RFID code to tag now? (y/n): ").lower().strip()
            if write_tag == "y":
                self._write_rfid_code(rfid_code)

            return True

        except Exception as e:
            print(f"\n✗ Error creating product: {e}")
            return False

    def _upload_image(self, product_id):
        """Upload and save product image."""
        while True:
            image_input = input("Image file path: ").strip()

            if not Path(image_input).exists():
                print("File not found. Try again.")
                continue

            try:
                from PIL import Image

                # Load and verify image
                img = Image.open(image_input)
                img.verify()

                # Save to product_images directory
                ext = Path(image_input).suffix
                dest_path = self.image_dir / f"product_{product_id}{ext}"
                img = Image.open(image_input)
                img.thumbnail((128, 64), Image.Resampling.LANCZOS)
                img.save(dest_path)

                print(f"✓ Image saved to: {dest_path}")
                return str(dest_path)

            except Exception as e:
                print(f"Error processing image: {e}")
                continue

    def _write_rfid_code(self, rfid_code):
        """Write RFID code to tag."""
        if not self.rfid_reader:
            print("✗ RFID reader not available")
            return False

        print("\nPlace blank RFID tag on reader...")
        try:
            success = self.rfid_reader.write_tag(rfid_code)
            if success:
                print(f"✓ RFID code written successfully: {rfid_code}")
                return True
            else:
                print("✗ Failed to write RFID code")
                return False

        except Exception as e:
            print(f"✗ Error writing RFID tag: {e}")
            return False

    def list_products(self):
        """List all products in database."""
        products = self.db.get_all_products()

        if not products:
            print("\nNo products found in database")
            return

        print("\n" + "="*80)
        print("PRODUCT DATABASE")
        print("="*80)

        for product in products:
            print(f"\nID: {product['id']}")
            print(f"  Name: {product['product_name']}")
            print(f"  RFID Code: {product['rfid_code']}")
            print(f"  Description: {product['product_description']}")
            print(f"  Type: {product['product_type']}")
            print(f"  Characteristics: {product['product_characteristics']}")
            if product['image_path']:
                print(f"  Image: {product['image_path']}")
            print("-" * 80)

    def write_product_to_tag(self):
        """Write existing product RFID code to a new tag."""
        if not self.rfid_reader:
            print("✗ RFID reader not available")
            return

        self.list_products()

        product_id = input("\nEnter Product ID to write to tag: ").strip()

        try:
            product = self.db.get_product_by_rfid(product_id)
            if not product:
                # Try by product ID instead
                products = self.db.get_all_products()
                product = next(
                    (p for p in products if str(p["id"]) == product_id), None
                )

            if not product:
                print("Product not found")
                return

            print(f"\nWriting to tag for: {product['product_name']}")
            print("Place blank RFID tag on reader...")

            success = self.rfid_reader.write_tag(product["rfid_code"])
            if success:
                print(f"✓ RFID code written: {product['rfid_code']}")
                self.db.log_rfid_write(product["id"])
            else:
                print("✗ Failed to write to RFID tag")

        except Exception as e:
            print(f"✗ Error: {e}")

    def run_menu(self):
        """Run interactive menu."""
        while True:
            print("\n" + "="*50)
            print("RFID PRODUCT SYSTEM - MANAGEMENT TOOL")
            print("="*50)
            print("1. Create new product")
            print("2. List all products")
            print("3. Write product code to RFID tag")
            print("4. Exit")
            print("="*50)

            choice = input("\nSelect option (1-4): ").strip()

            if choice == "1":
                self.interactive_create_product()
            elif choice == "2":
                self.list_products()
            elif choice == "3":
                self.write_product_to_tag()
            elif choice == "4":
                print("\nGoodbye!")
                break
            else:
                print("Invalid option. Try again.")


def main():
    """Main entry point for standalone tool."""
    tool = StandaloneTool()
    tool.run_menu()


if __name__ == "__main__":
    main()