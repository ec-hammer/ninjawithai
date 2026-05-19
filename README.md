# RFID Product Display System

A comprehensive Python system for managing products using RFID tags and displaying product information on a cheap yellow OLED display.

## Features

### 1. **Database Module** (`database_module.py`)
- SQLite-based product storage
- Unique RFID code per product
- Product information: name, description, characteristics, images, custom fields
- Product management (CRUD operations)

### 2. **RFID Module** (`rfid_module.py`)
- PN532 NFC reader/writer support
- UART and I2C interface support
- Continuous scanning (1 second intervals)
- Debouncing logic:
  - Requires 2 seconds stability for new tag recognition
  - Displays "Searching..." for unstable reads
  - Shows "No Information" after 3 seconds if tag not found
- Tag writing capability

### 3. **Display Module** (`display_module.py`)
- OLED display management (128x64 recommended)
- Automatic field rotation (5 seconds per field)
- Displays:
  - Product name
  - Description
  - Characteristics
  - Type
  - Custom option fields
  - Product images
- Status messages: Searching, No Information, Ready

### 4. **Standalone Tool** (`standalone_tool.py`)
- Interactive product record creation
- Image upload and optimization
- RFID code generation
- Tag writing
- Product database management

## Hardware Requirements

- **ESP32 with Yellow OLED Display** (128x64 SH1106)
- **PN532 NFC Module** (I2C interface)
- **Python 3.8+**

## Installation

### 1. Clone or download the project

```bash
git clone <repository-url>
cd rfid-product-system
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure I2C and Serial (Raspberry Pi/Linux)

```bash
# Enable I2C
sudo raspi-config
# Interface Options -> I2C -> Enable

# Check I2C devices
i2cdetect -y 1

# Check serial ports
ls /dev/tty*
```

### 4. Update hardware configuration in `config.py`

```python
RFID_SERIAL_PORT = "/dev/ttyUSB0"  # Or your serial port
DISPLAY_I2C_ADDRESS = 0x3C         # Check with i2cdetect
```

## Usage

### Creating Products (Standalone Tool)

```bash
python standalone_tool.py
```

Follow the interactive menu to:
1. Create new product records
2. Upload product images
3. Generate unique RFID codes
4. Write codes to RFID tags
5. View all products

### Running the Main System

```bash
# Normal operation
python main.py

# Demo mode (no RFID hardware needed)
python main.py --demo

# Using display simulator
python main.py --simulator
```

### Demo Mode Commands

In demo mode, you can test the display functionality:
- `1` - Show sample product 1
- `2` - Show sample product 2
- `3` - Show "Searching" state
- `4` - Show "No Information" state
- `5` - Show "Ready" state
- `q` - Quit

## System Flow

1. **Scan RFID Tag**
   - System continuously scans for RFID tags (1 second intervals)

2. **Debounce Check**
   - Display shows "Searching..." while tag is unstable
   - After 2 seconds of stable reading, accepts the tag

3. **Database Lookup**
   - Queries SQLite database with RFID code

4. **Display Product**
   - Shows product information
   - Rotates through fields every 5 seconds
   - Cycles: Name → Description → Characteristics → Type → Options → Image

5. **Tag Change**
   - New tag detected triggers immediate search
   - Previous product display stops
   - Process repeats from step 1

## Database Schema

### Products Table
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    rfid_code TEXT UNIQUE,
    product_name TEXT,
    product_description TEXT,
    product_type TEXT,
    product_characteristics TEXT,
    image_path TEXT,
    option_field_1 TEXT,
    option_field_2 TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### RFID Write History Table
```sql
CREATE TABLE rfid_write_history (
    id INTEGER PRIMARY KEY,
    product_id INTEGER,
    written_at TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
)
```

## API Reference

### DatabaseModule

```python
db = DatabaseModule("products.db")

# Create product
product_id = db.create_product(
    rfid_code="ABC123XYZ",
    product_name="Product Name",
    product_description="Description",
    product_type="Type",
    product_characteristics="Characteristics"
)

# Get product by RFID
product = db.get_product_by_rfid("ABC123XYZ")

# Get all products
all_products = db.get_all_products()

# Update product
db.update_product(product_id, product_name="New Name")

# Generate unique RFID code
code = db.generate_unique_rfid_code()
```

### RFIDModule

```python
rfid_reader = PN532Reader(interface_type="i2c")
rfid = RFIDModule(
    rfid_reader,
    scan_interval=1.0,
    debounce_stable=2.0,
    callback=my_callback_function
)

rfid.start()
# ... system running ...
rfid.stop()

# Read current tag
tag = rfid.get_current_tag()

# Get state
state, tag = rfid.get_tag_state()  # Returns: ('idle'|'searching'|'found'|'no_info', tag_data)

# Write to tag
success = rfid.write_tag("ABC123XYZ")
```

### DisplayModule

```python
display = DisplayModule(
    width=128,
    height=64,
    field_duration=5,
    use_simulator=False
)

display.start()

# Show product (auto-rotates fields)
display.show_product(product_dict)

# Show status
display.show_searching()
display.show_no_information()
display.show_idle()

display.stop()
```

## Troubleshooting

### RFID Reader Not Found
- Check I2C connection: `i2cdetect -y 1`
- Verify PN532 is powered and connected
- Check `config.py` I2C address

### Display Not Showing
- Check I2C address with `i2cdetect -y 1`
- Verify SH1106 OLED display is connected
- Run in simulator mode to test: `python main.py --simulator`

### Serial Port Issues
- List available ports: `ls /dev/tty*`
- Update `config.py` with correct port
- Check permissions: `sudo usermod -a -G dialout $USER`

### Database Locked
- Ensure only one instance of the system is running
- Delete `products.db` if corrupted (will recreate on startup)

## Customization

### Adjust Debounce Timing
Edit `config.py`:
```python
RFID_SCAN_INTERVAL = 1.0        # Scan frequency
RFID_DEBOUNCE_STABLE = 2.0      # Stability requirement
RFID_NO_INFO_TIMEOUT = 3.0      # No info timeout
```

### Change Display Duration
```python
DISPLAY_FIELD_DURATION = 5  # Seconds per field
```

### Add Custom Fields
Edit `database_module.py` and add columns to products table, then reference them in `display_module.py`.

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Logging
All events are logged to:
- Console output
- `rfid_system.log` file

Change log level in `config.py`:
```python
LOG_LEVEL = "DEBUG"  # For verbose output
```

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the logs in `rfid_system.log`
3. Run in demo/simulator mode to isolate hardware issues

## Version History

- **v1.0.0** - Initial release
  - Core database, RFID, and display modules
  - Standalone product management tool
  - Demo mode for testing