import os
import kagglehub
from kagglehub import KaggleDatasetAdapter
import pandas as pd
from os import getenv
import psycopg2
import psycopg2.pool
import sys
import mysql.connector
from mysql.connector import pooling

# Variables de entorno
POSTGRES = getenv("POSTGRES")
POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
POSTGRES_DB = getenv("POSTGRES_DB")

MARIADB = os.getenv("MARIADB")
MARIADB_USER = os.getenv("MARIADB_USER")
MARIADB_PASS = os.getenv("MARIADB_PASS")
MARIADB_DB = os.getenv("MARIADB_DB")


print(f"POSTGRES: {POSTGRES}")
print(f"POSTGRES_USER: {POSTGRES_USER}")
print(f"POSTGRES_DB: {POSTGRES_DB}")
print(f"POSTGRES_PASSWORD: {POSTGRES_PASSWORD}")

print(f"MARIADB: {MARIADB}")
print(f"MARIADB_USER: {MARIADB_USER}")
print(f"MARIADB_DB: {MARIADB_DB}")
print(f"MARIADB_PASS: {MARIADB_PASS}")

def load_dataset():
    try:
        df = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "iamsouravbanerjee/animal-information-dataset",
            "Animal Dataset.csv"
        )
        print(f"Dataset cargado: {len(df)} registros")
        return df
    except Exception as e:
        print(f"Error cargando dataset: {e}")
        raise

# Crear pool de conexiones PostgreSQL
try:
    pg_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=5,
        host=POSTGRES,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB
    )
    print("Pool de conexiones PostgreSQL creado")
except Exception as e:
    print(f"Error creando pool PostgreSQL: {e}")
    sys.exit(1)

def execute_postgress_from_file():    
    # Construir la ruta al archivo
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(script_dir, 'schemas', 'postgres.sql')    
    try:
        with open(schema_path, 'r', encoding='utf-8') as file:
            schema_sql = file.read()
        print("Archivo leído correctamente")
    except FileNotFoundError:
        print(f"Archivo no encontrado en: {schema_path}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    conn = pg_pool.getconn()
    cur = conn.cursor()
    
    try:
        cur.execute(schema_sql)
        conn.commit()
        print("Tablas creadas exitosamente en PostgreSQL")
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        cur.close()
        pg_pool.putconn(conn)

def insert_data_postgres(df):    
    conn = pg_pool.getconn()
    cur = conn.cursor()
    
    try:
        for index, row in df.iterrows():
            cur.execute("""
                INSERT INTO dieta (tipo_dieta) VALUES (%s) 
                ON CONFLICT (tipo_dieta) DO NOTHING
            """, (row["Diet"],))
            cur.execute("SELECT id FROM dieta WHERE tipo_dieta=%s", (row["Diet"],))
            dieta_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO familia (nombre_familia) VALUES (%s) 
                ON CONFLICT (nombre_familia) DO NOTHING
            """, (row["Family"],))
            cur.execute("SELECT id FROM familia WHERE nombre_familia=%s", (row["Family"],))
            familia_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO animal (nombre, altura_cm, peso_kg, color, esperanza_vida_años, dieta_id, familia_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (
                row["Animal"], row["Height (cm)"], row["Weight (kg)"], row["Color"],
                row["Lifespan (years)"], dieta_id, familia_id
            ))
            animal_id = cur.fetchone()[0]

            habitats = [h.strip() for h in str(row["Habitat"]).split(",") if h.strip()]
            for h in habitats:
                if h and h.lower() != 'nan':
                    cur.execute("""
                        INSERT INTO habitat (nombre_habitat) VALUES (%s) 
                        ON CONFLICT (nombre_habitat) DO NOTHING
                    """, (h,))
                    cur.execute("SELECT id FROM habitat WHERE nombre_habitat=%s", (h,))
                    habitat_id = cur.fetchone()[0]
                    cur.execute("""
                        INSERT INTO animal_habitat (animal_id, habitat_id) VALUES (%s, %s) 
                        ON CONFLICT (animal_id, habitat_id) DO NOTHING
                    """, (animal_id, habitat_id))

            predadores = [p.strip() for p in str(row["Predators"]).split(",") if p.strip()]
            for p in predadores:
                if p and p.lower() != 'nan':
                    cur.execute("""
                        INSERT INTO predador (nombre_predador) VALUES (%s) 
                        ON CONFLICT (nombre_predador) DO NOTHING
                    """, (p,))
                    cur.execute("SELECT id FROM predador WHERE nombre_predador=%s", (p,))
                    predador_id = cur.fetchone()[0]
                    cur.execute("""
                        INSERT INTO animal_predador (animal_id, predador_id) VALUES (%s, %s) 
                        ON CONFLICT (animal_id, predador_id) DO NOTHING
                    """, (animal_id, predador_id))

            cur.execute("""
                INSERT INTO info_extra (animal_id, velocidad_prom_kmh, velocidad_max_kmh, paises_encontrado,
                estado_conservacion, gestacion_dias, estructura_social, crias_por_parto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                animal_id, row["Average Speed (km/h)"], row["Top Speed (km/h)"], row["Countries Found"],
                row["Conservation Status"], row["Gestation Period (days)"], row["Social Structure"], row["Offspring per Birth"]
            ))

        conn.commit()
        print(f"Registros insertados exitosamente")
        return True
        
    except Exception as e:
        print(f"Error insertando datos: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        pg_pool.putconn(conn)

#-------------------------------------Maria DB------------------------------------- 

# Crear pool de conexiones MariaDB
try:
    mariadb_pool = pooling.MySQLConnectionPool(
        pool_name="mariadb_pool",
        pool_size=5,
        host=MARIADB,
        user=MARIADB_USER,
        password=MARIADB_PASS,
        database=MARIADB_DB,
        charset='utf8mb4',          
        collation='utf8mb4_general_ci', 
        autocommit=True
    )
    print("Pool de conexiones MariaDB creado")
except Exception as e:
    print(f"Error creando pool MariaDB: {e}")
    sys.exit(1)

def execute_MariaDB_from_file():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(script_dir, 'schemas', 'mariadb.sql')    
    try:
        with open(schema_path, 'r', encoding='utf-8') as file:
            schema_sql = file.read()
        print("Archivo leído correctamente")
    except FileNotFoundError:
        print(f"Archivo no encontrado en: {schema_path}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    conn = mariadb_pool.get_connection()
    cur = conn.cursor()
    
    try:
        for statement in schema_sql.split(";"):
            stmt = statement.strip()
            if stmt:
                cur.execute(stmt)
        conn.commit()
        print("Tablas creadas exitosamente en MariaDB")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error creando tablas de MariaDB: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def insert_data_mariadb(df):
    conn = mariadb_pool.get_connection()
    cur = conn.cursor()
    try:
        for index, row in df.iterrows():
            cur.execute("""
                INSERT IGNORE INTO dieta (tipo_dieta) VALUES (%s)
            """, (row["Diet"],))
            cur.execute("SELECT id FROM dieta WHERE tipo_dieta=%s", (row["Diet"],))
            dieta_id = cur.fetchone()[0]

            cur.execute("""
                INSERT IGNORE INTO familia (nombre_familia) VALUES (%s)
            """, (row["Family"],))
            cur.execute("SELECT id FROM familia WHERE nombre_familia=%s", (row["Family"],))
            familia_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO animal (nombre, altura_cm, peso_kg, color, esperanza_vida_años, dieta_id, familia_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                row["Animal"], row["Height (cm)"], row["Weight (kg)"], row["Color"],
                row["Lifespan (years)"], dieta_id, familia_id
            ))
            animal_id = cur.lastrowid  

            habitats = [h.strip() for h in str(row["Habitat"]).split(",") if h.strip()]
            for h in habitats:
                if h and h.lower() != 'nan':
                    cur.execute("""
                        INSERT IGNORE INTO habitat (nombre_habitat) VALUES (%s)
                    """, (h,))
                    cur.execute("SELECT id FROM habitat WHERE nombre_habitat=%s", (h,))
                    habitat_id = cur.fetchone()[0]
                    cur.execute("""
                        INSERT IGNORE INTO animal_habitat (animal_id, habitat_id) VALUES (%s, %s)
                    """, (animal_id, habitat_id))

            predadores = [p.strip() for p in str(row["Predators"]).split(",") if p.strip()]
            for p in predadores:
                if p and p.lower() != 'nan':
                    cur.execute("""
                        INSERT IGNORE INTO predador (nombre_predador) VALUES (%s)
                    """, (p,))
                    cur.execute("SELECT id FROM predador WHERE nombre_predador=%s", (p,))
                    predador_id = cur.fetchone()[0]
                    cur.execute("""
                        INSERT IGNORE INTO animal_predador (animal_id, predador_id) VALUES (%s, %s)
                    """, (animal_id, predador_id))

            cur.execute("""
                INSERT INTO info_extra (animal_id, velocidad_prom_kmh, velocidad_max_kmh, paises_encontrado,
                estado_conservacion, gestacion_dias, estructura_social, crias_por_parto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                animal_id, row["Average Speed (km/h)"], row["Top Speed (km/h)"], row["Countries Found"],
                row["Conservation Status"], row["Gestation Period (days)"], row["Social Structure"], row["Offspring per Birth"]
            ))

        conn.commit()
        print("Registros insertados exitosamente en MariaDB")
        return True

    except Exception as e:
        conn.rollback()
        print(f"Error insertando datos en MariaDB: {e}")
        return False
    finally:
        cur.close()
        conn.close()




    

if __name__ == "__main__":    
    try:
        # Ejecutar schema 
        if not execute_postgress_from_file():
            print("No se pudieron crear las tablas en PostgreSQL")
            sys.exit(1)

        elif not execute_MariaDB_from_file():
            print("No se pudieron crear las tablas en MariaDB")
            sys.exit(1)
        
        # Cargar dataset
        df = load_dataset()
        
        # Insertar datos
        if insert_data_postgres(df) and insert_data_mariadb(df):
            print("DataSeeder completado exitosamente en PostgreSQL y MariaDB")
        else:
            print("Error insertando datos")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error general: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("DataSeeder terminado")