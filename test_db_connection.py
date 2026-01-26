import mysql.connector
from mysql.connector import Error

# Configuration - UPDATED WITH USER CREDENTIALS
DB_CONFIG = {
    "user": "8f61a9239b0145c99a4ded6b29d50f12",
    "password": "9259f46dd3a55372d29261f327748ea1068b33549e309c47af17a73b448ba800",
    "host": "f6b184ab-ac1e-478b-b599-9a69e347d50b.br38q28f0334iom5lv4g.databases.appdomain.cloud",
    "port": 31306,
    "database": "eshtri"
}

print("="*50)
print(f"Testing connection to remote DB...")
print(f"   Host: {DB_CONFIG['host']}")
print(f"   Port: {DB_CONFIG['port']}")
print("="*50)

try:
    connection = mysql.connector.connect(**DB_CONFIG)
    if connection.is_connected():
        db_info = connection.get_server_info()
        print(f"SUCCESS! Connected to MySQL Server version {db_info}")
        
        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print(f"You're connected to database: {record[0]}")
        
        # List tables to be sure
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
            
except Error as e:
    print(f"\nCONNECTION FAILED")
    print(f"Error Code: {e.errno}")
    print(f"Message: {e.msg}")

finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("\nConnection closed.")
