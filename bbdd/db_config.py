# db_config.py
import psycopg
from psycopg import sql
from psycopg import OperationalError
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

def ejecutar_schema_si_necesario(cur):
    # Verificar si la tabla 'usuarios' existe
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'usuarios'
        );
    """)
    existe = cur.fetchone()[0]

    if not existe:
        print("📦 Ejecutando schema.sql para crear las tablas...")
        if not os.path.isfile(SCHEMA_PATH):
            print(f"❌ No se encontró el archivo '{SCHEMA_PATH}'")
            return

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
            cur.execute(schema_sql)
            cur.connection.commit()
            print("✅ Tablas creadas correctamente.")
    else:
        print("✔️ Tablas ya existentes. No se ejecutó schema.sql.")

def conectar_db():
    try:
        # Solo crear la base si no existe, pero NO ejecutar el schema aquí
        crear_base_de_datos()
        conn = psycopg.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except OperationalError as e:
        raise ConnectionError(f"No se pudo conectar a la base de datos:\n{e}")
