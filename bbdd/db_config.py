# db_config.py
from psycopg import sql, OperationalError, connect
import ctypes
import os, configparser

config = configparser.ConfigParser()
config.read("bbdd/arjenix_config.ini")

DB_NAME = config.get("DB", "name")
DB_USER = config.get("DB", "user")
DB_PASSWORD = config.get("DB", "password")
DB_HOST = config.get("DB", "host")
DB_PORT = config.get("DB", "port")
SCHEMA_PATH = "bbdd/schema.sql"

def crear_base_de_datos():
    with connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    ) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (DB_NAME,))
            existe = cur.fetchone()

            if not existe:
                print(f"ℹ️ La base de datos '{DB_NAME}' no existe. Creándola...")
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
                print("✅ Base creada con éxito.")

                # 2. Conectarse ahora a arjenix para ejecutar el schema
                with connect(
                    dbname=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    host=DB_HOST,
                    port=DB_PORT
                ) as nueva_conn:
                    with nueva_conn.cursor() as cur_schema:
                        ejecutar_schema(cur_schema)

def ejecutar_schema(cur):
    if not os.path.isfile(SCHEMA_PATH):
        ctypes.windll.user32.MessageBoxW(0, f"No se encontró el archivo '{SCHEMA_PATH}'", "Advertencia", 0x30)
        return

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

        for stmt in schema_sql.split(";"):
            stmt = stmt.strip()
            try:
                cur.execute(stmt)
                cur.connection.commit()
                if "CREATE TABLE IF NOT EXISTS" in stmt:
                    # Extraer nombre de la tabla entre 'EXISTS' y '('
                    inicio = stmt.upper().find("EXISTS") + len("EXISTS")
                    fin = stmt.find("(")
                    nombre = stmt[inicio:fin].strip()
                    print(f"✅ Tabla {nombre} creada con éxito.")
                
            except Exception as e:
                print(f"⚠️ Error al crear las tablas. Error: {e}")

        print("✅ Tablas creada con éxito.") 

def conectar_db():
    try:
        crear_base_de_datos()  # Solo crea si no existe
        conn = connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except OperationalError as e:
        raise ConnectionError(f"No se pudo conectar a la base de datos:\n{e}")
