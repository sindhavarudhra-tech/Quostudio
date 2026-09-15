import psycopg2
import csv
import os

DB_CONFIG = {
    "dbname": "quotation_maker",
    "user": "rudhrasindhava",
    "password": "",
    "host": "127.0.0.1",
    "port": "5432"
}

def run_clean_import():
    if not os.path.exists('master_inventory.csv'):
        print("ERROR: Could not find 'master_inventory.csv'.")
        return

    # NEW: Check for cloud database URL first
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        conn = psycopg2.connect(db_url)
    else:
        conn = psycopg2.connect(**DB_CONFIG)
        
    cursor = conn.cursor()
    # ... (Keep the rest of your table creation and import code exactly the same below this)

    print("Setting up database tables...")
    # 1. Categories Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        );
    ''')
    
    # Ensure default categories 1 to 7 exist
    default_categories = [
        (1, 'General Inventory'),
        (2, 'Fruit Plants'),
        (3, 'Flowering & Pooja Related'),
        (4, 'Creepers'),
        (5, 'Avenue Flowering & Shade Trees'),
        (6, 'Palm Trees'),
        (7, 'Ornamental Trees')
    ]
    for cat_id, cat_name in default_categories:
        cursor.execute('''
            INSERT INTO categories (id, name)
            VALUES (%s, %s)
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;
        ''', (cat_id, cat_name))

    # 2. Items Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            botanical_name VARCHAR(255) NOT NULL,
            common_name VARCHAR(255),
            dsr VARCHAR(255),
            height VARCHAR(100),
            spread VARCHAR(100),
            spacing VARCHAR(100),
            effect VARCHAR(255),
            price NUMERIC(10, 2) DEFAULT 0.0,
            category_id INTEGER REFERENCES categories(id) DEFAULT 1
        );
    ''')

    print("Wiping existing items and restarting IDs...")
    cursor.execute('TRUNCATE TABLE items RESTART IDENTITY CASCADE;')
    
    print("Importing plants from master_inventory.csv...")
    insert_count = 0

    with open('master_inventory.csv', 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        
        # Clean column headers by stripping whitespace
        reader.fieldnames = [name.strip() if name else '' for name in reader.fieldnames]

        for row in reader:
            # Safely clean row keys and values
            clean_row = {k.strip(): (v.strip() if v else '') for k, v in row.items() if k}

            # Price handling
            price_raw = clean_row.get('Price', '0').replace(',', '').replace('₹', '').strip()
            try:
                price_val = float(price_raw) if price_raw and price_raw != '-' else 0.0
            except ValueError:
                price_val = 0.0

            # Category ID handling:
            # If '-', empty, or invalid, assign to 1 (General Inventory).
            cat_raw = clean_row.get('Category_ID') or clean_row.get('Category') or clean_row.get('category_id') or '1'
            cat_raw = cat_raw.strip()

            if cat_raw in ['-', '', 'None', 'null']:
                cat_id = 1
            else:
                try:
                    cat_num = int(float(cat_raw))
                    cat_id = cat_num if 1 <= cat_num <= 7 else 1
                except ValueError:
                    cat_id = 1

            cursor.execute('''
                INSERT INTO items (
                    botanical_name, common_name, dsr, height, spread, 
                    spacing, effect, price, category_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                clean_row.get('Botanical Name', ''),
                clean_row.get('Common Name', ''),
                clean_row.get('DSR', ''),
                clean_row.get('Height', ''),
                clean_row.get('Spread', ''),
                clean_row.get('Spacing', ''),
                clean_row.get('Effect', ''),
                price_val,
                cat_id
            ))
            insert_count += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Success! {insert_count} plants imported with clean category mappings.")

if __name__ == '__main__':
    run_clean_import()