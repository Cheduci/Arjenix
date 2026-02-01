import os, configparser
from psycopg import sql, OperationalError, connect
import ctypes

base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, "arjenix_config.ini")
SCHEMA_PATH = os.path.join(base_dir, "schema.sql")
DB_NAME = "arjenix"  # hardcoded

def verificar_ini():
    """Garantiza que el archivo ini exista y tenga la sección [DB]."""
    config = configparser.ConfigParser()

    # Si no existe, lo creo con campos vacíos
    if not os.path.isfile(config_path):
        config["DB"] = {
            "name": DB_NAME,
            "user": "",
            "password": "",
            "host": "",
            "port": ""
        }
        with open(config_path, "w") as f:
            config.write(f)

    config.read(config_path)

    # Si no tiene sección [DB], la agrego
    if "DB" not in config:
        config["DB"] = {
            "name": DB_NAME,
            "user": "",
            "password": "",
            "host": "",
            "port": ""
        }
        with open(config_path, "w") as f:
            config.write(f)

    return config["DB"]

def crear_base_de_datos(db):
    with connect(
        dbname="postgres",
        user=db["user"],
        password=db["password"],
        host=db["host"],
        port=db["port"]
    ) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (DB_NAME,))
            existe = cur.fetchone()
            if not existe:
                print(f"ℹ️ La base de datos '{DB_NAME}' no existe. Creándola...")
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
                print("✅ Base creada con éxito.")
                with connect(
                    dbname=DB_NAME,
                    user=db["user"],
                    password=db["password"],
                    host=db["host"],
                    port=db["port"]
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
        if stmt:
            try:
                cur.execute(stmt)
                cur.connection.commit()
            except Exception as e:
                print(f"⚠️ Error al crear las tablas. Error: {e}")
    print("✅ Tablas creadas con éxito.")

def conectar_db():
    try:
        db = verificar_ini()

        # Si faltan campos, devolvemos error para que la app abra el diálogo
        if not all([db.get("user"), db.get("password"), db.get("host"), db.get("port")]):
            raise ConnectionError("El archivo arjenix_config.ini está incompleto. Debe completarse.")

        crear_base_de_datos(db)
        conn = connect(
            dbname=DB_NAME,
            user=db["user"],
            password=db["password"],
            host=db["host"],
            port=db["port"]
        )
        return conn
    except OperationalError as e:
        raise ConnectionError(f"No se pudo conectar a la base de datos:\n{e}")
