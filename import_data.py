import pandas as pd
import psycopg2
import numpy as np

# 1. Read the CSV file (using latin-1 encoding to prevent decoding crashes)
df = pd.read_csv('The Plant Tender Inventory.csv', encoding='latin-1')

# 2. Replace empty strings, whitespace-only cells, and NaN values with Python None (which translates to NULL in PostgreSQL)
df = df.replace(r'^\s*$', np.nan, regex=True)
df = df.where(pd.notnull(df), None)

# 3. Clean the Price column safely
def clean_price(val):
    if val is None:
        return 0.0
    # Remove currency symbols, commas, etc.
    cleaned = str(val).replace(',', '').replace('₹', '').replace('€', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

df['Clean_Price'] = df['Unit Price'].apply(clean_price)

# 4. Connect to your local PostgreSQL database using psycopg2
conn = psycopg2.connect(
    dbname="quotation_maker",
    user="rudhrasindhava",
    password="",
    host="127.0.0.1",
    port="5432"
)
cursor = conn.cursor()

# 5. Delete/Truncate the entire table and reset ID counter to 1
cursor.execute("TRUNCATE TABLE items RESTART IDENTITY CASCADE;")
print("Table 'items' truncated successfully. All old data removed.")

# 6. Loop through the dataframe and insert rows, handling NULLs properly
insert_query = """
    INSERT INTO items (sr_no, botanical_name, common_name, dsr_code, height, spread, spacing, effect, canes, price)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

for index, row in df.iterrows():
    # Helper to extract values safely, converting NaN/None to Python None (SQL NULL)
    def get_val(col_name):
        val = row.get(col_name)
        if pd.isna(val) or val is None or str(val).strip() == '':
            return None
        return str(val).strip()

    sr_no = row.get('Sr.no')
    sr_no_val = int(sr_no) if pd.notna(sr_no) and str(sr_no).isdigit() else None

    botanical = get_val('Botanical Name')
    if not botanical:
        continue  # Skip rows without a botanical name

    common = get_val('Common Name')
    dsr = get_val('DSR Code')
    height = get_val('Height (ft)')
    spread = get_val('Spread (m)')
    spacing = get_val('Spacing (m c/c)')
    effect = get_val('Effect')
    canes = get_val('Canes')
    price = row['Clean_Price']

    cursor.execute(insert_query, (
        sr_no_val, botanical, common, dsr, height, spread, spacing, effect, canes, price
    ))

# 7. Commit changes and close connections
conn.commit()
cursor.close()
conn.close()

print("All plant data successfully imported into PostgreSQL with empty boxes set to NULL!")