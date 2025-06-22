from . import config
import psycopg
import os

def existe_db():
    try:
        with psycopg.connect(
            dbname="postgres",
            user=config.user,
            password=config.password,
            host=config.host,
            port=config.port,
            autocommit=True
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (config.dbname,))
                return cur.fetchone() is not None
    except Exception as e:
        print(f"❌ Error al verificar la existencia de la base de datos: {e}")
        return False

def crear_db():
    try:
        with psycopg.connect(
            dbname="postgres",
            user=config.user,
            password=config.password,
            host=config.host,
            port=config.port,
            autocommit=True
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE {config.dbname};")
                print(f"✅ Base de datos '{config.dbname}' creada.")
    except Exception as e:
        print(f"❌ Error al crear la base de datos: {e}")

def conectar_db():
    try:
        conn = psycopg.connect(
            dbname=config.dbname,
            user=config.user,
            password=config.password,
            host=config.host,
            port=config.port
        )
        print(f"🔌 Conectado a '{config.dbname}'")
        return conn
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
        return None

def create_table(conn, schema_path=None):
    try:
        # Ruta al esquema
        if schema_path is None:
            base_path = os.path.dirname(os.path.abspath(__file__))
            schema_path = os.path.normpath(os.path.join(base_path, "..", "BBDD", "schema.sql"))

        # Verificar si el archivo existe
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"No se encontró el archivo: {schema_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        with conn.cursor() as cur:
            cur.execute(schema_sql)
            conn.commit()
            print("✅ Tablas creadas correctamente.")

    except Exception as e:
        print(f"❌ Error al crear las tablas: {e}")
        conn.rollback()