"""
Database Module - SQLite-based product storage with RFID codes
"""

import sqlite3
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseModule:
    def __init__(self, db_path="products.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create database tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create products table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rfid_code TEXT UNIQUE NOT NULL,
                    product_name TEXT NOT NULL,
                    product_description TEXT,
                    product_type TEXT,
                    product_characteristics TEXT,
                    image_path TEXT,
                    option_field_1 TEXT,
                    option_field_2 TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Create RFID write history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS rfid_write_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    written_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
                """
            )

            conn.commit()
            logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def create_product(
        self,
        rfid_code,
        product_name,
        product_description="",
        product_type="",
        product_characteristics="",
        image_path="",
        option_field_1="",
        option_field_2="",
    ):
        """Create a new product record."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO products 
                (rfid_code, product_name, product_description, product_type,
                 product_characteristics, image_path, option_field_1, option_field_2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rfid_code,
                    product_name,
                    product_description,
                    product_type,
                    product_characteristics,
                    image_path,
                    option_field_1,
                    option_field_2,
                ),
            )

            conn.commit()
            product_id = cursor.lastrowid
            logger.info(f"Product created with ID: {product_id}, RFID: {rfid_code}")
            return product_id

        except sqlite3.IntegrityError as e:
            logger.error(f"RFID code already exists: {rfid_code}")
            raise
        except sqlite3.Error as e:
            logger.error(f"Database error creating product: {e}")
            raise

    def get_product_by_rfid(self, rfid_code):
        """Retrieve product by RFID code."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM products WHERE rfid_code = ?", (rfid_code,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

        except sqlite3.Error as e:
            logger.error(f"Database error retrieving product: {e}")
            return None

    def get_all_products(self):
        """Retrieve all products."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Database error retrieving products: {e}")
            return []

    def update_product(self, product_id, **kwargs):
        """Update a product record."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build dynamic update query
            allowed_fields = [
                "product_name",
                "product_description",
                "product_type",
                "product_characteristics",
                "image_path",
                "option_field_1",
                "option_field_2",
            ]

            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            if not updates:
                return False

            updates["updated_at"] = datetime.now()

            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [product_id]

            cursor.execute(
                f"UPDATE products SET {set_clause} WHERE id = ?",
                values,
            )

            conn.commit()
            logger.info(f"Product {product_id} updated")
            return True

        except sqlite3.Error as e:
            logger.error(f"Database error updating product: {e}")
            return False

    def delete_product(self, product_id):
        """Delete a product record."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()

            logger.info(f"Product {product_id} deleted")
            return True

        except sqlite3.Error as e:
            logger.error(f"Database error deleting product: {e}")
            return False

    def generate_unique_rfid_code(self):
        """Generate a unique RFID code (timestamp-based)."""
        import hashlib

        timestamp = datetime.now().isoformat()
        code = hashlib.md5(timestamp.encode()).hexdigest()[:16].upper()
        return code

    def log_rfid_write(self, product_id):
        """Log RFID write operation."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO rfid_write_history (product_id) VALUES (?)",
                (product_id,),
            )

            conn.commit()
            logger.info(f"RFID write logged for product {product_id}")

        except sqlite3.Error as e:
            logger.error(f"Error logging RFID write: {e}")