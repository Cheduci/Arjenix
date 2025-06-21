from . import config
import psycopg
from psycopg import OperationalError
from psycopg.rows import dict_row
import random
import os
import cv2
from datetime import datetime
import unicodedata

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

    
def table_exists(conn, table_name):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table_name,))
            return cursor.fetchone()[0]
    except Exception as e:
        print(f"⚠ Error al verificar la tabla '{table_name}': {e}")
        return False

def create_table(conn, schema_path=None):
    try:
        # Ruta al esquema
        if schema_path is None:
            base_path = os.path.dirname(os.path.abspath(__file__))
            schema_path = os.path.join(base_path, "..", "BBDD", "schema.sql")
            schema_path = os.path.normpath(schema_path)

        if table_exists(conn, "productos") and table_exists(conn, "categorias"):
            print("ℹ️ Las tablas ya existen. No se creó nada.")
            return

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

class GeneradorEAN13:
    def __init__(self, cursor, prefijo="77999"):
        self.cursor = cursor
        self.prefijo = prefijo

    def calcular_digito_verificador(self, ean12: str) -> str:
        suma = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(ean12))
        return str((10 - suma % 10) % 10)

    def generar_codigo_unico(self) -> str:
        while True:
            secuencia = f"{random.randint(0, 999999):06d}"
            ean12 = self.prefijo + secuencia
            digito = self.calcular_digito_verificador(ean12)
            ean13 = ean12 + digito

            self.cursor.execute("SELECT 1 FROM productos WHERE codigo_barra = %s", (ean13,))
            if not self.cursor.fetchone():
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
            nombre_limpio = unicodedata.normalize("NFKD", nombre_producto).encode("ascii", "ignore").decode()
            archivo = f"{nombre_producto}_{timestamp}.jpg".replace(" ", "_")
            path = os.path.join(carpeta, archivo)
            cv2.imwrite(path, frame)
            print(f"Foto capturada y guardada como {archivo}.")
            cap.release()
            cv2.destroyAllWindows()
            return path
        elif key == 27:  # ESC
            print("🚫 Captura cancelada.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

def listar_categorias(cur):
    cur.execute("SELECT id, nombre FROM categorias ORDER BY nombre;")
    return cur.fetchall()

def agregar_categoria(cur, nombre):
    cur.execute("INSERT INTO categorias (nombre) VALUES (%s) RETURNING id;", (nombre,))
    return cur.fetchone()[0]

def eliminar_categoria(cur, id_categoria):
    cur.execute("SELECT nombre FROM categorias WHERE id = %s;", (id_categoria,))
    fila = cur.fetchone()
    if fila:
        nombre = fila[0]
        cur.execute("DELETE FROM categorias WHERE id = %s;", (id_categoria,))
        return nombre
    return None

def categoria_existe(cur, id_categoria):
    cur.execute("SELECT 1 FROM categorias WHERE id = %s;", (id_categoria,))
    return cur.fetchone() is not None

def solicitar_datos_producto(cur):
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

    def seleccionar_categoria(cur):
        while True:
            # Mostrar lista actual
            categorias = listar_categorias(cur)
            
            print("\n📂 Categorías disponibles:")
            for id_, nombre in categorias:
                print(f"  {id_:>3} - {nombre}")
            
            print("\nOpciones:")
            print("  [ID] para seleccionar una categoría")
            print("  [A] para agregar una nueva categoría")
            print("  [B] para eliminar una categoría")
            eleccion = input("Seleccionar opción: ").strip()

            if eleccion.lower() == "a":
                nombre_nueva = input("🔤 Ingrese el nombre de la nueva categoría: ").strip().capitalize()
                if not nombre_nueva:
                    print("⚠️ El nombre no puede estar vacío.")
                    continue
                try:
                    nueva_id = agregar_categoria(cur,nombre_nueva)
                    print(f"✅ Categoría '{nombre_nueva}' agregada con ID {nueva_id}.")
                    
                except Exception as e:
                    print(f"❌ Error al agregar categoría: {e}")
                    continue

            elif eleccion.lower() == "b":
                try:
                    id_eliminar = int(input("🗑 Ingrese el ID de la categoría a eliminar: ").strip())
                    cur.execute("SELECT nombre FROM categorias WHERE id = %s;", (id_eliminar,))
                    fila = cur.fetchone()
                    if fila:
                        nombre = fila[0]
                        confirmar = input(f"¿Estás seguro de que querés eliminar la categoría '{nombre}' (ID {id_eliminar})? [s/n]: ").strip().lower()
                        if confirmar == "s":
                            nombre_eliminado = eliminar_categoria(cur,id_eliminar)
                            print(f"✅ Categoría '{nombre_eliminado}' eliminada.")
                        else:
                            print("🚫 Eliminación cancelada.")
                    else:
                        print("⚠️ No existe una categoría con ese ID.")
                except ValueError:
                    print("⚠️ Debe ingresar un número válido.")
                except Exception as e:
                    print(f"❌ Error al eliminar: {e}")

            else:
                try:
                    id_seleccionada = int(eleccion)
                    if categoria_existe(cur, id_seleccionada):
                        return id_seleccionada
                    print("⚠️ El ID ingresado no corresponde a ninguna categoría.")
                except ValueError:
                    print("❌ Opción inválida. Ingrese un número, A o B.")

    def leer_imagen_binaria(path):
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
        return None

    print("\n🛒 Ingrese los datos del nuevo producto:")
    nombre = pedir_texto("nombre del producto")
    categoria_id = seleccionar_categoria(cur)
    precio_compra = pedir_float("precio de compra")
    precio_venta = pedir_float("precio de venta")
    stock_actual = pedir_entero("stock actual")
    stock_minimo = pedir_opcional_entero("stock mínimo")
    foto_path = capturar_foto(nombre)
    foto_bytes = leer_imagen_binaria(foto_path)

    generador = GeneradorEAN13(cur)
    codigo_barra = generador.generar_codigo_unico()

    return {
        "nombre": nombre,
        "categoria_id": categoria_id,
        "codigo_barra": codigo_barra,
        "precio_compra": precio_compra,
        "precio_venta": precio_venta,
        "stock_actual": stock_actual,
        "stock_minimo": stock_minimo,
        "foto": foto_bytes
    }

def insertar_producto(cur, datos):
    try:
        cur.execute("""
            INSERT INTO productos (
                nombre,
                categoria_id,
                codigo_barra,
                precio_compra,
                precio_venta,
                stock_actual,
                stock_minimo,
                foto
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datos["nombre"],
            datos["categoria_id"],
            datos["codigo_barra"],
            datos["precio_compra"],
            datos["precio_venta"],
            datos["stock_actual"],
            datos["stock_minimo"],
            datos["foto"]
        ))
        print(f"✅ Producto '{datos['nombre']}' insertado con éxito.")

    except Exception as e:
        print(f"❌ Error al insertar producto: {e}")
