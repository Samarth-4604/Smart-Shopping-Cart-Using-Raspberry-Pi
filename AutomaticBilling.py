#AutomaticBilling.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from rpi_lcd import LCD
from PIL import Image
from escpos.printer import Usb
import time
from datetime import datetime

# 1. Google Sheets setup
#    - Download your service‑account key JSON and save it as 'credentials.json'
#    - Share your Google Sheet with the service account email (Editor access)
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
# 👉 Replace "Your_Spreadsheet_Name" with the exact name of your Google Sheet
sheet = client.open("Your_Spreadsheet_Name").sheet1


# 2. LCD (Raspberry Pi) setup
#    - Make sure you have an LCD connected and the rpi_lcd library installed
lcd = LCD()


# 3. Thermal printer setup
#    - Replace 0xXXXX, 0xYYYY with your printer’s USB Vendor ID and Product ID
printer = Usb(0xXXXX, 0xYYYY)


def resize_qr_image(path, size=(400, 400)):
    """
    Open and resize a QR code image.
    """
    img = Image.open(path)
    return img.resize(size)


def print_qr_code(printer, image_path):
    """
    Print the resized QR code on the thermal printer.
    """
    qr_img = resize_qr_image(image_path)
    printer.image(qr_img)


def get_item_details(barcode):
    """
    Look up an item by its barcode in the Google Sheet.
    Returns (item_name, price) if found, else (None, None).
    """
    records = sheet.get_all_records()
    for row in records:
        if str(row.get("Barcode")) == str(barcode):
            return row.get("Item Name"), row.get("Price")
    return None, None


def scan_items():
    """
    Main loop:
      1. Display a welcome message on the LCD.
      2. Scan barcodes until the user types 'n'.
      3. Show each item’s name and price on console + LCD.
      4. Calculate total and print a receipt with a QR code.
    """
    # Welcome message
    lcd.clear()
    lcd.text("Welcome!", 1)
    lcd.text("Scan items...", 2)
    time.sleep(2)

    total_price = 0.0
    scanned_items = {}  # { item_name: [quantity, price] }

    while True:
        code = input("Scan a barcode (or 'n' to finish): ").strip()
        if code.lower() == "n":
            break

        name, price = get_item_details(code)
        if name:
            price = float(price)
            # Update quantity
            if name in scanned_items:
                scanned_items[name][0] += 1
            else:
                scanned_items[name] = [1, price]

            qty = scanned_items[name][0]
            total_price = sum(q * p for q, p in scanned_items.values())

            # Show on console and LCD
            print(f"{name} x{qty} @Rs.{price:.2f} = Rs.{qty*price:.2f}")
            lcd.clear()
            lcd.text(name, 1)
            lcd.text(f"Rs.{price:.2f}", 2)
        else:
            print("Item not found.")
            lcd.clear()
            lcd.text("Item not found!", 1)
            time.sleep(2)

    # Final total display
    print(f"\nTotal: Rs.{total_price:.2f}")
    lcd.clear()
    lcd.text(f"Total: Rs.{total_price:.2f}", 1)
    lcd.text("Printing bill...", 2)
    time.sleep(2)

    # Print receipt
    printer.text("Your Shop Name\n")
    printer.text(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
    printer.text("----------------------------\n")
    for name, (qty, price) in scanned_items.items():
        printer.text(f"{name} x{qty} @Rs.{price:.2f} = Rs.{qty*price:.2f}\n")
    printer.text("----------------------------\n")
    printer.text(f"TOTAL: Rs.{total_price:.2f}\n")
    printer.text("Scan QR to pay\n")

    # 👉 Replace "paymentQr.jpg" with your QR code image filename
    print_qr_code(printer, "paymentQr.jpg")

    printer.text("\nThank you!\n")
    printer.cut()

    # Goodbye message
    lcd.clear()
    lcd.text("Thank you!", 1)
    lcd.text("Visit again!", 2)
    time.sleep(3)
    lcd.clear()


if name == "__main__":
    scan_items()
