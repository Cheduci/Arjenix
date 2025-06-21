from . import config
import psycopg
from psycopg import OperationalError
from psycopg.rows import dict_row
import random
import os
import cv2
from datetime import datetime
import unicodedata
import webbrowser
import tempfile
import barcode
from barcode import get as get_barcode
from barcode.writer import ImageWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import numpy as np
from pyzbar.pyzbar import decode


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
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error al abrir la cámara.")
        return None

    print("📸 Presione ESPACIO para capturar o ESC para cancelar.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Error al capturar la imagen.")
            break

        cv2.imshow("Vista previa - Cámara", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 32:  # ESPACIO
            nombre_limpio = unicodedata.normalize("NFKD", nombre_producto).encode("ascii", "ignore").decode()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            cv2.imwrite(archivo_temp.name, frame)
            cap.release()
            cv2.destroyAllWindows()
            print(f"✅ Foto capturada.")
            return archivo_temp.name
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
            valor = input(f"Ingrese {campo}: ").strip().capitalize()
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
                contenido = f.read()
            try:
                os.remove(path)
                print(f"🧹 Imagen temporal eliminada: {path}")
            except Exception as e:
                print(f"⚠️ No se pudo borrar la imagen temporal: {e}")
            return contenido
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

def mostrar_todos_los_productos(cur):
    try:
        cur.execute("""
            SELECT id, nombre, stock_actual, precio_venta
            FROM productos
            ORDER BY nombre;
        """)
        productos = cur.fetchall()

        if not productos:
            print("⚠️ No hay productos registrados.")
            return

        print("\n🧾 Lista de productos:")
        print(f"{'ID':>3} | {'Nombre':<25} | {'Stock':>5} | {'Precio':>8}")
        print("-" * 50)
        for id_, nombre, stock, precio in productos:
            print(f"{id_:>3} | {nombre:<25} | {stock:>5} | ${precio:>7.2f}")
        print("-" * 50)

        # Nueva sección interactiva
        while True:
            print("\nOpciones:")
            print("[A] Seleccionar un producto")
            print("[B] Volver al menú")
            eleccion = input("Seleccione una opción: ").strip().lower()

            if eleccion == "a":
                try:
                    id_prod = int(input("Ingrese el ID del producto: ").strip())
                    mostrar_ficha_producto(cur, id_prod)
                except ValueError:
                    print("⚠️ Ingrese un número válido.")
                break
            elif eleccion == "b":
                break
            else:
                print("❌ Opción no válida.")


    except Exception as e:
        print(f"❌ Error al consultar productos: {e}")

def consultar_por_categoria(cur):
    try:
        cur.execute("SELECT id, nombre FROM categorias ORDER BY nombre;")
        categorias = cur.fetchall()
        if not categorias:
            print("⚠️ No hay categorías registradas.")
            return
        
        print("\n📂 Categorías disponibles:")
        for id_, nombre in categorias:
            print(f"  {id_:>3} - {nombre}")
        
        id_cat = input("Seleccione el ID de la categoría: ").strip()
        if not id_cat.isdigit():
            print("⚠️ Debe ingresar un número válido.")
            return
        
        cur.execute("""
            SELECT id, nombre, stock_actual, precio_venta
            FROM productos
            WHERE categoria_id = %s
            ORDER BY nombre;
        """, (int(id_cat),))
        productos = cur.fetchall()

        if not productos:
            print("⚠️ No hay productos en esa categoría.")
            return

        print(f"\n📦 Productos en categoría ID {id_cat}:")
        print(f"{'ID':>3} | {'Nombre':<25} | {'Stock':>5} | {'Precio':>8}")
        print("-" * 50)
        for id_, nombre, stock, precio in productos:
            print(f"{id_:>3} | {nombre:<25} | {stock:>5} | ${precio:>7.2f}")
        print("-" * 50)

        # Nueva sección interactiva
        while True:
            print("\nOpciones:")
            print("[A] Seleccionar un producto")
            print("[B] Volver al menú")
            eleccion = input("Seleccione una opción: ").strip().lower()

            if eleccion == "a":
                try:
                    id_prod = int(input("Ingrese el ID del producto: ").strip())
                    mostrar_ficha_producto(cur, id_prod)
                except ValueError:
                    print("⚠️ Ingrese un número válido.")
                break
            elif eleccion == "b":
                break
            else:
                print("❌ Opción no válida.")


    except Exception as e:
        print(f"❌ Error al consultar por categoría: {e}")

def consultar_por_stock(cur):
    def mostrar_productos(productos):
        if not productos:
            print("⚠️ No se encontraron productos en ese criterio.")
            return
        print(f"\n📦 Resultados:")
        print(f"{'ID':>3} | {'Nombre':<25} | {'Stock':>5} | {'Precio':>8}")
        print("-" * 50)
        for id_, nombre, stock, precio in productos:
            print(f"{id_:>3} | {nombre:<25} | {stock:>5} | ${precio:>7.2f}")
        print("-" * 50)

        # Nueva sección interactiva
        while True:
            print("\nOpciones:")
            print("[A] Seleccionar un producto")
            print("[B] Volver al menú")
            eleccion = input("Seleccione una opción: ").strip().lower()

            if eleccion == "a":
                try:
                    id_prod = int(input("Ingrese el ID del producto: ").strip())
                    mostrar_ficha_producto(cur, id_prod)
                except ValueError:
                    print("⚠️ Ingrese un número válido.")
                break
            elif eleccion == "b":
                break
            else:
                print("❌ Opción no válida.")

    concepto_abundante = 100
    while True:
        print("\n📊 CONSULTA POR STOCK")
        print("[1] Productos sin stock (stock = 0)")
        print("[2] Por debajo del stock mínimo")
        print(f"[3] Stock abundante (stock >= {concepto_abundante})")
        print("[0] Volver")
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "0":
            break
        elif opcion == "1":
            cur.execute("""
                SELECT id, nombre, stock_actual, precio_venta
                FROM productos
                WHERE stock_actual = 0
                ORDER BY nombre;
            """)
            mostrar_productos(cur.fetchall())
        elif opcion == "2":
            cur.execute("""
                SELECT id, nombre, stock_actual, precio_venta
                FROM productos
                WHERE stock_minimo IS NOT NULL AND stock_actual <= stock_minimo
                ORDER BY nombre;
            """)
            mostrar_productos(cur.fetchall())
        elif opcion == "3":
            cur.execute(f"""
                SELECT id, nombre, stock_actual, precio_venta
                FROM productos
                WHERE stock_actual >= {concepto_abundante}
                ORDER BY stock_actual DESC;
            """)
            mostrar_productos(cur.fetchall())
        else:
            print("❌ Opción inválida.")

def consultar_por_precio(cur):
    while True:
        minimo = input("💰 Precio mínimo (ENTER para omitir): ").strip()
        maximo = input("💰 Precio máximo (ENTER para omitir): ").strip()

        min_val = float(minimo) if minimo.replace(".", "", 1).isdigit() else None
        max_val = float(maximo) if maximo.replace(".", "", 1).isdigit() else None

        if min_val is None and minimo:
            print("⚠️ El mínimo debe ser un número válido o estar vacío.")
            continue
        if max_val is None and maximo:
            print("⚠️ El máximo debe ser un número válido o estar vacío.")
            continue
        if min_val is not None and max_val is not None and min_val > max_val:
            print("⚠️ El mínimo no puede ser mayor que el máximo.")
            continue

        # Construir cláusula SQL dinámica
        query = "SELECT id, nombre, stock_actual, precio_venta FROM productos WHERE TRUE"
        params = []
        if min_val is not None:
            query += " AND precio_venta >= %s"
            params.append(min_val)
        if max_val is not None:
            query += " AND precio_venta <= %s"
            params.append(max_val)
        query += " ORDER BY precio_venta;"

        try:
            cur.execute(query, tuple(params))
            productos = cur.fetchall()
            if not productos:
                print("⚠️ No se encontraron productos en ese rango.")
            else:
                rango = ""
                if min_val is not None and max_val is not None:
                    rango = f"${min_val:.2f} a ${max_val:.2f}"
                elif min_val is not None:
                    rango = f"mayores a ${min_val:.2f}"
                elif max_val is not None:
                    rango = f"menores a ${max_val:.2f}"
                else:
                    rango = "todos los precios"

                print(f"\n📦 Productos ({rango}):")
                print(f"{'ID':>3} | {'Nombre':<25} | {'Stock':>5} | {'Precio':>8}")
                print("-" * 50)
                for id_, nombre, stock, precio in productos:
                    print(f"{id_:>3} | {nombre:<25} | {stock:>5} | ${precio:>7.2f}")
                print("-" * 50)

                # Nueva sección interactiva
                while True:
                    print("\nOpciones:")
                    print("[A] Seleccionar un producto")
                    print("[B] Volver al menú")
                    eleccion = input("Seleccione una opción: ").strip().lower()

                    if eleccion == "a":
                        try:
                            id_prod = int(input("Ingrese el ID del producto: ").strip())
                            mostrar_ficha_producto(cur, id_prod)
                        except ValueError:
                            print("⚠️ Ingrese un número válido.")
                        break
                    elif eleccion == "b":
                        break
                    else:
                        print("❌ Opción no válida.")
            break
        except Exception as e:
            print(f"❌ Error al consultar por precio: {e}")
            break

def buscar_producto(cur):
    while True:
        print("\n🔎 BUSCAR PRODUCTO")
        print("[1] Buscar por nombre")
        print("[2] Buscar por código de barras")
        print("[0] Volver")
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "0":
            break
        elif opcion == "1":
            texto = input("Ingrese parte del nombre: ").strip()
            if not texto:
                print("⚠️ El texto no puede estar vacío.")
                continue
            cur.execute("""
                SELECT id, nombre, stock_actual, precio_venta
                FROM productos
                WHERE nombre ILIKE %s
                ORDER BY nombre;
            """, (f"%{texto}%",))
            productos = cur.fetchall()
        elif opcion == "2":
            usar_escaneo = input("¿Escanear código con cámara? [s/n]: ").strip().lower()
            if usar_escaneo == "s":
                codigo = escanear_codigo_opencv()
            else:
                codigo = input("Ingrese el código o parte del código manualmente: ").strip()
            
            if not codigo:
                print("⚠️ El código no puede estar vacío.")
                continue
            cur.execute("""
                SELECT id, nombre, stock_actual, precio_venta
                FROM productos
                WHERE codigo_barra ILIKE %s
                ORDER BY nombre;
            """, (f'%{codigo}%',))
            productos = cur.fetchall()

        else:
            print("❌ Opción inválida.")
            continue

        if not productos:
            print("⚠️ No se encontraron coincidencias.")
        else:
            print("\n📦 Resultados de búsqueda:")
            print(f"{'ID':>3} | {'Nombre':<25} | {'Stock':>5} | {'Precio':>8}")
            print("-" * 50)
            for id_, nombre, stock, precio in productos:
                print(f"{id_:>3} | {nombre:<25} | {stock:>5} | ${precio:>7.2f}")
            print("-" * 50)

            # Nueva sección interactiva
            while True:
                print("\nOpciones:")
                print("[A] Seleccionar un producto")
                print("[B] Volver al menú")
                eleccion = input("Seleccione una opción: ").strip().lower()

                if eleccion == "a":
                    try:
                        id_prod = int(input("Ingrese el ID del producto: ").strip())
                        mostrar_ficha_producto(cur, id_prod)
                    except ValueError:
                        print("⚠️ Ingrese un número válido.")
                    break
                elif eleccion == "b":
                    break
                else:
                    print("❌ Opción no válida.")

def escanear_codigo_opencv():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ No se pudo acceder a la cámara.")
        return None

    print("📷 Escaneando... Presione ESC para cancelar.")
    codigo_detectado = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Error al capturar imagen.")
            break

        decoded_objs = decode(frame)

        for obj in decoded_objs:
            puntos = obj.polygon
            if len(puntos) > 4:
                hull = cv2.convexHull(
                    np.array([p for p in puntos], dtype=np.float32)
                )
                hull = list(map(tuple, np.squeeze(hull)))
            else:
                hull = puntos

            cv2.polylines(frame, [np.array(hull, dtype=np.int32)], True, (0, 255, 0), 2)
            x = int(hull[0][0])
            y = int(hull[0][1]) - 10
            cv2.putText(frame, obj.data.decode("utf-8"), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 255, 50), 2)
            codigo_detectado = obj.data.decode("utf-8")

        cv2.imshow("Escaneo de código", frame)
        key = cv2.waitKey(1) & 0xFF

        if codigo_detectado and len(codigo_detectado) == 13:
            codigo_detectado = codigo_detectado[:12]
            print(f"✅ Código detectado: {codigo_detectado}")
            break
        if key == 27:  # ESC
            print("🚫 Escaneo cancelado.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return codigo_detectado

def mostrar_ficha_producto(cur, producto_id):
    try:
        cur.execute("""
            SELECT p.nombre, p.codigo_barra, p.precio_compra, p.precio_venta,
                   p.stock_actual, p.stock_minimo, c.nombre AS categoria,
                   p.foto IS NOT NULL AS tiene_foto
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.id = %s;
        """, (producto_id,))
        prod = cur.fetchone()
        if not prod:
            print("❌ Producto no encontrado.")
            return

        (nombre, codigo, compra, venta, stock, minimo, categoria, tiene_foto) = prod
        print("\n🧾 Ficha del producto")
        print("──────────────────────")
        print(f"📌 Nombre: {nombre}")
        print(f"🏷️  Código EAN13: {codigo}")
        print(f"📂 Categoría: {categoria if categoria else 'Sin asignar'}")
        print(f"💰 Precio de compra: ${compra:.2f}")
        print(f"💸 Precio de venta:  ${venta:.2f}")
        print(f"📦 Stock actual: {stock} unidades")
        print(f"📉 Stock mínimo: {minimo if minimo is not None else '—'}")
        print(f"{'📸 Foto disponible' if tiene_foto else '🖼️ Sin foto'}")

        if tiene_foto:
            ver = input("¿Desea ver la foto? [s/n]: ").strip().lower()
            if ver == "s":
                guardar_y_abrir_foto(cur, producto_id)

        exportar = input("🖨️ ¿Exportar código de barras a PDF? [s/n]: ").strip().lower()
        if exportar == "s":
            while True:
                cantidad = input("¿Cuántas etiquetas desea generar? ").strip()
                if cantidad.isdigit() and int(cantidad) > 0:
                    exportar_codigo_pdf(nombre, codigo, venta, cantidad)
                    
                    break
                else:
                    print("Ingrese un número entero")

    except Exception as e:
        print(f"❌ Error al mostrar el producto: {e}")

def guardar_y_abrir_foto(cur, producto_id):
    cur.execute("SELECT foto FROM productos WHERE id = %s;", (producto_id,))
    fila = cur.fetchone()
    if fila and fila[0]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(fila[0])
            tmp_path = tmp.name
        webbrowser.open(tmp_path)
    else:
        print("⚠️ El producto no tiene una foto guardada.")

def exportar_codigo_pdf(nombre, codigo, precio, cantidad):
    try:
        cantidad = int(cantidad)
        if cantidad <= 0:
            print("⚠️ La cantidad debe ser mayor a cero.")
            return

        # Dimensiones
        etiquetas_por_fila = 5
        etiquetas_por_columna = 8
        max_etiquetas = etiquetas_por_fila * etiquetas_por_columna  # 40 por hoja
        etiquetas_a_imprimir = min(cantidad, max_etiquetas)

        # Generar código de barras como imagen PNG temporal
        tmp_path_base = tempfile.mktemp()
        ean = barcode.get('ean13', codigo, writer=ImageWriter())
        imagen_path = ean.save(tmp_path_base)

        # Preparar PDF
        pdf_path = os.path.join(os.getcwd(), f"etiquetas_{codigo}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A4)
        pagina_ancho, pagina_alto = A4

        margen_izq = 40
        margen_sup = 60
        espaciado_x = 100
        espaciado_y = 60

        for i in range(etiquetas_a_imprimir):
            fila = i // etiquetas_por_fila
            col = i % etiquetas_por_fila
            x = margen_izq + col * espaciado_x
            y = pagina_alto - margen_sup - fila * espaciado_y

            c.drawInlineImage(imagen_path, x, y + 3, width=80, height=30)  # Imagen primero, Más arriba

            c.setFont("Helvetica", 8)
            c.drawString(x, y - 3, nombre[:25])  # Más separado hacia abajo del código
            c.drawString(x, y - 15, f"${precio:.2f}")



        c.showPage()
        c.save()

        os.remove(imagen_path)
        webbrowser.open(pdf_path)
        print(f"✅ PDF generado: {pdf_path}")

        if cantidad > etiquetas_a_imprimir:
            print(f"ℹ️ Se generó una hoja con {etiquetas_a_imprimir}. Podés imprimir {cantidad // etiquetas_a_imprimir} copias para cubrir la cantidad deseada.")

    except Exception as e:
        print(f"❌ Error al generar etiquetas: {e}")

def consultar_productos(cur):
    while True:
        print("\n📦 CONSULTAR PRODUCTOS")
        print("══════════════════════════")
        print("[1] Ver todos los productos")
        print("[2] Filtrar por categoría")
        print("[3] Filtrar por stock")
        print("[4] Filtrar por precio")
        print("[5] Buscar por nombre o código")
        print("[0] Volver al menú principal")
        opcion = input("Seleccione una opción: ").strip()
        if opcion == "0":
            break
        elif opcion == "1":
            mostrar_todos_los_productos(cur)
        elif opcion == "2":
            consultar_por_categoria(cur)
        elif opcion == "3":
            consultar_por_stock(cur)
        elif opcion == "4":
            consultar_por_precio(cur)
        elif opcion == "5":
            buscar_producto(cur)
        else:
            print("❌ Opción inválida.")
