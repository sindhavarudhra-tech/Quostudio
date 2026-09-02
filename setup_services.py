import psycopg2

# Database connection details
DB_CONFIG = {
    "dbname": "quotation_maker",
    "user": "rudhrasindhava",
    "password": "",
    "host": "127.0.0.1",
    "port": "5432"
}

def setup_services():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 1. Create the services table
    cursor.execute("""
        DROP TABLE IF EXISTS services;
        CREATE TABLE services (
            id SERIAL PRIMARY KEY,
            description TEXT NOT NULL,
            price NUMERIC(15, 2) NOT NULL,
            unit_type VARCHAR(50)
        );
    """)

    # 2. Prepare the exact data from your quotation image
    services_data = [
        ("Fine Grading", 3.50, "per sqft"),
        ("Garden Development (Small plant)", 30.00, "per plant"),
        ("Garden Development (Big plant)", 100.00, "per plant"),
        ("After Maintainance (2-3 months old plantation)", 150000.00, "per month"),
        ("Extra Charge (Pot and plantation)", 20.00, "per plant"),
        ("Lawn Cutting", 15000.00, "per month"),
        ("Pesticides and Fertilizer", 15000.00, "per month"),
        ("Transportation Charges", 3000.00, "per tonne")
    ]

    # 3. Insert the data into PostgreSQL
    insert_query = "INSERT INTO services (description, price, unit_type) VALUES (%s, %s, %s)"
    cursor.executemany(insert_query, services_data)

    conn.commit()
    cursor.close()
    conn.close()
    print("Success! The 'services' table has been created and populated.")

if __name__ == '__main__':
    setup_services()