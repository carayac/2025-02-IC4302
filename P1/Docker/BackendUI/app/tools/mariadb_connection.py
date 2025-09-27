#Imports from mariadb module
import mariadb
import sys
import os
import logging

logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

#Environment variables for database connection
DB_HOST = os.getenv("MARIADB")
DB_USER = os.getenv("MARIADB_USER")
DB_PASSWORD = os.getenv("MARIADB_PASS")

#mariadb connection pool
mariadb_pool = None

#Function to create a connection to the MariaDB database
def init_connection():
    global mariadb_pool
    try:
        mariadb_pool = mariadb.ConnectionPool(
            pool_name="mypool",
            pool_size=5,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=3306,
            database="promptsy"
        )
    except mariadb.Error as e:
        logger.info("Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

#Function to execute a query and return the results witout repeat logic
def execute_query(query, params=None,fetch_one=False):
    global mariadb_pool
    conn = None
    cursor = None
    try:
        conn = mariadb_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        #check if the query is a SELECT statement to do a fetch
        if query.strip().lower().startswith("select"):
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()
        else:
            #this is for INSERT, UPDATE, DELETE statements it returns the number of affected rows
            return cursor.rowcount

    except mariadb.Error as e:
        logger.error(f"Error executing query: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

#initialize the connection pool when the module is imported
init_connection()        