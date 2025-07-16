# db_config.py
import psycopg
from psycopg import sql, OperationalError
from PySide6.QtWidgets import QMessageBox
import os

DB_NAME = "arjenix"
DB_USER = "postgres"
DB_PASSWORD = "39416072"
DB_HOST = "127.0.0.1"
DB_PORT = "5432"
SCHEMA_PATH = "bbdd/schema.sql"

def crear_base_de_datos():
    conn = psycopg.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Verificar si ya existe
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (DB_NAME,))
    existe = cur.fetchone()

    if not existe:
        print(f"ℹ️ La base de datos '{DB_NAME}' no existe. Creándola...")
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
        print("✅ Base creada con éxito.")

    cur.close()
    conn.close()

def ejecutar_schema(cur):
    if not os.path.isfile(SCHEMA_PATH):
        QMessageBox.warning(None, "Advertencia", f"No se encontró el archivo '{SCHEMA_PATH}'")
        return

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

        for stmt in schema_sql.split(";"):
            stmt = stmt.strip()
            if "CREATE TABLE IF NOT EXISTS" in stmt.upper():
                tipo = "Tabla"
                inicio = stmt.find("EXISTS") + len("EXISTS")
                fin = stmt.find("(")
                nombre = stmt[inicio:fin].strip()
            elif "CREATE INDEX IF NOT EXISTS" in stmt.upper():
                tipo = "Índice"
                inicio = stmt.find("EXISTS") + len("EXISTS")
                fin = stmt.find("ON")
                nombre = stmt[inicio:fin].strip()
            try:
                cur.execute(stmt)
                cur.connection.commit()
                
            except Exception as e:
                print(f"⚠️ Error al crear las tablas. Error: {e}")

        print("✅ Tablas creada con éxito.") 

def conectar_db():
    try:
        crear_base_de_datos()  # Solo crea si no existe
        conn = psycopg.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        ejecutar_schema(cur)  # SIEMPRE ejecuta el schema
        return conn
    except OperationalError as e:
        raise ConnectionError(f"No se pudo conectar a la base de datos:\n{e}")
