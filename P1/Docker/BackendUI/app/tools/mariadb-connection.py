#Imports from mariadb module
import mariadb
import sys
import os

#Environment variables for database connection
DB_HOST = os.getenv("MARIADB")
DB_USER = os.getenv("MARIADB_USER")
DB_PASSWORD = os.getenv("MARIADB_PASS")

#mariadb connection pool
mariadb_pool = None

#Function to create a connection to the MariaDB database
def init_connection():
    try:
        pool = mariadb.ConnectionPool(
            pool_name="mypool",
            pool_size=5,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=3306,
            database="promptsy"
        )
        mariadb_pool = pool
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

#initialize the connection pool when the module is imported
init_connection()        