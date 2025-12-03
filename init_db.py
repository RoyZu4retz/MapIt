import mysql.connector

# --- Database Connection Settings ---
# Make sure your MySQL server is running!
config = {
    'user': 'root',
    'password': 'Roeroe99RzA!',  # Put your MySQL root password here
    'host': '127.0.0.1',
    'database': 'cities'  # The schema you just created
}


conn = None
cursor = None
try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    print("Connected to MySQL database 'world_db'")

    # 1. We NO LONGER DROP the table.
    #    We'll use CREATE TABLE IF NOT EXISTS.
    #    Since the table exists, this line will do nothing.
    print("Ensuring 'cities' table exists...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cities (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(255) NOT NULL,
            country VARCHAR(255) NOT NULL,
            latitude DECIMAL(9, 6) NOT NULL,
            longitude DECIMAL(9, 6) NOT NULL,
            level INT NOT NULL
        )
    ''')

    # 2. Insert the new 300-city list
    print(f"Adding {len(cities_to_add)} new cities to the table...")
    insert_query = '''
        INSERT INTO cities (name, country, latitude, longitude, level)
        VALUES (%s, %s, %s, %s, %s)
    '''
    cursor.executemany(insert_query, cities_to_add)

    conn.commit()
    print(f"Successfully added {cursor.rowcount} new cities.")

    # Get and print the new total count
    cursor.execute("SELECT COUNT(*) FROM cities")
    total_count = cursor.fetchone()[0]
    print(f"There are now {total_count} total cities in the database.")


except mysql.connector.Error as err:
    print(f"Error: {err}")
finally:
    if 'conn' in locals() and conn.is_connected():
        if 'cursor' in locals():
            cursor.close()
        conn.close()
        print("MySQL connection closed.")