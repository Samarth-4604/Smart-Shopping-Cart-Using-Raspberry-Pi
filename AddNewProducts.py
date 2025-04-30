#AddNewProducts.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. Define which Google APIs we need access to
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 2. Load your service‑account credentials
#    👉 Replace 'credentials.json' with the path to your JSON keyfile
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

# 3. Authorize and create the gspread client
client = gspread.authorize(creds)

# 4. Open your Google Sheet and select the first worksheet
#    👉 Replace 'Your_Spreadsheet_Name' with the exact name of your sheet
sheet = client.open("Your_Spreadsheet_Name").sheet1


def get_item_details(barcode):
    """
    Look up an item by its barcode in the sheet.
    Returns (item_name, price) if found, otherwise (None, None).
    """
    # Read all rows as a list of dicts: each dict maps column names to values
    records = sheet.get_all_records()
    for row in records:
        # Compare both values as strings just in case
        if str(row.get("Barcode")) == str(barcode):
            return row.get("Item Name"), row.get("Price")
    # Not found
    return None, None


def add_new_barcode(barcode, item_name, price):
    """
    Add a new row to the sheet for a barcode we haven’t seen.
    """
    # Append a row [Barcode, Item Name, Price]
    sheet.append_row([barcode, item_name, price])
    print(f"Added new item: {item_name} — Rs.{price}")


def main():
    # Ask the user to scan or type a barcode
    barcode = input("Enter or scan a barcode: ").strip()

    # Try to fetch existing details
    item_name, price = get_item_details(barcode)

    if item_name:
        # If found, just show it
        print(f"Item: {item_name}\nPrice: Rs.{price}")
    else:
        # If not found, prompt to add it
        print("Barcode not found in database.")
        new_name = input("Enter product name: ").strip()
        new_price = input("Enter product price: ").strip()

        # Simple check to ensure price looks numeric
        if new_name and new_price.replace('.', '', 1).isdigit():
            add_new_barcode(barcode, new_name, new_price)
        else:
            print("Invalid input. Please enter a valid name and numeric price.")


if name == "__main__":
    main()
