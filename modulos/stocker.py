import psycopg
from psycopg import OperationalError
from psycopg.rows import dict_row
from getpass import getpass
import random
import os
import cv2
from datetime import datetime

BD_name = "stocker"
DB_user = "postgres"
# DB_password = getpass("Ingrese la contraseña de la base de datos: ")
DB_password = "39416072"
DB_host = "localhost"
DB_port = "5432"

def connect_to_db():
    conn = None
    try:
        conn = psycopg.connect(
            dbname=BD_name,
            user=DB_user,
            password=DB_password,
            host=DB_host,
            port=DB_port,
            
        )
        print(f"Conexión exitosa a la base de datos {BD_name}.")
        return conn
    except OperationalError as e:
        # Si el error es específicamente que la DB no existe
        if "does not exist" in str(e):
            print(f"La base de datos '{BD_name}' no existe. Intentando crearla...")
            temp_conn = None
            try:
                # Intento 2: Conectar a una base de datos por defecto (como 'postgres')
                # para poder crear la nueva DB. El usuario DB_user debe tener permisos CREATEDB.
                temp_conn = psycopg.connect(
                    dbname="postgres", # Conectamos a 'postgres' o 'template1'
                    user=DB_user,
                    password=DB_password,
                    host=DB_host,
                    port=DB_port,
                    autocommit=True # <--- ¡Aquí se activa el autocommit en psycopg!
                )
                # Establecer autocommit para CREATE DATABASE
                cur = temp_conn.cursor()

                # Ejecutar el comando para crear la base de datos
                # Es crucial que DB_user tenga permiso para crear DBs o uses 'postgres' aquí
                cur.execute(f"CREATE DATABASE {BD_name} OWNER {DB_user};")
                print(f"Base de datos '{BD_name}' creada exitosamente.")
                cur.close()
                temp_conn.close()

                # Una vez creada, intenta conectar a la base de datos recién creada
                conn = psycopg.connect(
                    dbname=BD_name,
                    user=DB_user,
                    password=DB_password,
                    host=DB_host,
                    port=DB_port
                )
                print(f"Conexión exitosa a la base de datos '{BD_name}' (recién creada).")
                return conn

            except psycopg.Error as inner_e:
                print(f"Error al intentar crear la base de datos o conectar después de crearla: {inner_e}")
                if temp_conn:
                    temp_conn.close() # Asegurarse de cerrar la conexión temporal
                return None
        else:
            # Otros errores operacionales (credenciales incorrectas, host inaccesible, etc.)
            print(f"Error de conexión operacional no relacionado con la existencia de la DB: {e}")
            return None
    except psycopg.Error as e:
        # Cualquier otro error de psycopg2 (ej. un error de autenticación si no es un OperationalError específico)
        print(f"Error de base de datos general: {e}")
        return None
    
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None
    
def create_table(conn, schema_path="schema.sql"):
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        with conn.cursor() as cursor:
            cursor.execute(schema_sql)
            # cursor.execute( """CREATE TABLE IF NOT EXISTS productos (
            #     id SERIAL PRIMARY KEY,
            #     nombre VARCHAR(100) NOT NULL,
            #     categoria VARCHAR(50) NOT NULL,
            #     codigo_barra VARCHAR(50) NOT NULL UNIQUE,
            #     precio_compra NUMERIC(10, 2) NOT NULL,
            #     precio_venta NUMERIC(10, 2) NOT NULL,
            #     stock_actual INTEGER NOT NULL,
            #     stock_minimo INTEGER,
            #     foto BYTEA,
            #     fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            # )""")
        conn.commit()
        print("Tabla 'productos' creada exitosamente.")
    except Exception as e:
        print(f"Error al crear la tabla: {e}")
        conn.rollback()

def table_exists(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql.SQL("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'productos'
                )
            """))
            exists = cursor.fetchone()[0]
            return exists
    except Exception as e:
        print(f"Error al verificar la existencia de la tabla: {e}")
        return False

def calcular_digito_verificador(ean12: str) -> str:
    suma = sum(int(d) if i % 2 == 0 else int(d) * 3 for i, d in enumerate(ean12))
    digito = (10 - (suma % 10)) % 10
    return str(digito)

def generar_codigo_unico(cur) -> str:
    prefijo = "77999"
    while True:
        secuencia = f"{random.randint(0, 999999):06d}"
        base = prefijo + secuencia
        if len(base) != 11:
            continue
        ean12 = base.zfill(12)
        digito = calcular_digito_verificador(ean12)
        ean13 = ean12 + digito

        cur.execute("SELECT 1 FROM productos WHERE codigo_barra = %s", (ean13,))
        if not cur.fetchone():
            return ean13

def capturar_foto(nombre_producto):
    carpeta = os.path.join("bbdd", "fotos")
    os.makedirs(carpeta, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error al abrir la cámara.")
        return None
    
    print("Presione ESPACIO para capturar una foto o ESC para salir sin capturar.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error al capturar la imagen.")
            break
        
        cv2.imshow("Vista previa - Cámara", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 32:  # ESPACIO
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo = f"{nombre_producto}_{timestamp}.jpg".replace(" ", "_")
            path = os.path.join(carpeta, archivo)
            cv2.imwrite(path, frame)
            print(f"Foto capturada y guardada como {archivo}.")
            cap.release()
            cv2.destroyAllWindows()
            return path

def solicitar_datos_producto():
    def pedir_texto(campo):
        while True:
            valor = input(f"Ingrese {campo}: ").strip()
            if valor:
                return valor
            print(f"El campo {campo} no puede estar vacío.")

    def pedir_float(campo):
        while True:
            valor = input(f"Ingrese {campo} (número con punto decimal): ").strip()
            try:
                return float(valor)
            except ValueError:
                print(f"El campo {campo} debe ser un número válido.")
    
    def pedir_entero(campo):
        while True:
            valor = input(f"Ingrese {campo} (número entero): ").strip()
            try:
                return int(valor)
            except ValueError:
                print(f"El campo {campo} debe ser un número entero válido.")
    
    def pedir_opcional_entero(campo):
        while True:
            valor = input(f"Ingrese {campo} (opcional, número entero o ENTER para omitir): ").strip()
            if not valor:
                return None
            try:
                return int(valor)
            except ValueError:
                print(f"El campo {campo} debe ser un número entero válido o dejarlo vacío.")
                return None
            
    print("Ingrese los datos del nuevo producto:")
    nombre = pedir_texto("nombre del producto")
    categoria = pedir_texto("categoría")
    precio_compra = pedir_float("precio de compra")
    precio_venta = pedir_float("precio de venta")
    stock_actual = pedir_entero("stock actual")
    stock_minimo = pedir_opcional_entero("stock mínimo")
    foto_path = capturar_foto(nombre)

    return {
        "nombre": nombre,
        "categoria": categoria,
        "codigo_barra": generar_codigo_unico(),
        "precio_compra": precio_compra,
        "precio_venta": precio_venta,
        "stock_actual": stock_actual,
        "stock_minimo": stock_minimo,
        "foto_path": foto_path
    }

def new_product(conn, datos_producto):
    try:
        with conn.cursor() as cursor:
            foto_data = None
            if datos_producto["foto_path"] and os.path.exists(datos_producto["foto_path"]):
                with open(datos_producto["foto_path"], "rb") as f:
                    foto_data = f.read()

            cursor.execute("""
                INSERT INTO productos (nombre, categoria, codigo_barra, precio_compra, precio_venta, stock_actual, stock_minimo, foto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                datos_producto["nombre"],
                datos_producto["categoria"],
                datos_producto["codigo_barra"],
                datos_producto["precio_compra"],
                datos_producto["precio_venta"],
                datos_producto["stock_actual"],
                datos_producto["stock_minimo"],
                foto_data
            ))
                
        conn.commit()
        print("Producto agregado exitosamente.")
    except Exception as e:
        print(f"Error al agregar el producto: {e}")
        conn.rollback()

if __name__ == "__main__":
    conexion = connect_to_db()
    if conexion:
        print("\n¡Ya tienes una conexión válida para trabajar con tu base de datos!")   
        if not table_exists(conexion):
            create_table(conexion)
        else:
            print(f"La tabla 'productos' ya existe en la base de datos {BD_name}.")
       
    else:
        print("No se pudo establecer una conexión con la base de datos. Verifica los detalles de conexión.")