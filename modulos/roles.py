from .scaner import obtener_codigo_barra
from .stocker import capturar_foto, seleccionar_categoria, GeneradorEAN13, buscar_producto, consultar_productos
from .ventas import iniciar_venta
import cv2
import numpy as np
from io import BytesIO
from PIL import Image


def menu_vendedor(cur):
    while True:
        print("\n🛒 MENÚ VENDEDOR")
        print("[1] Iniciar nueva venta")
        print("[2] Buscar producto")
        print("[3] Consultar stock")
        print("[0] Cerrar sesión")

        opcion = input("Elegí una opción: ").strip()

        if opcion == "1":
            iniciar_venta(cur)
        elif opcion == "2":
            buscar_producto(cur)
        elif opcion == "3":
            consultar_productos(cur)
        elif opcion == "0":
            print("👋 Sesión cerrada.")
            break
        else:
            print("❌ Opción inválida.")


def menu_repositor(cur):
    while True:
        print("\n📦 MENÚ REPOSITOR")
        print("[1] Ingresar stock")
        print("[2] Consultar productos stock bajo")
        print("[3] Modificar precio de producto")
        print("[4] Ingreso nuevo producto")
        print("[0] Cerrar sesión")

        opcion = input("Opción: ").strip()

        if opcion == "1":
            ingresar_stock(cur)
        elif opcion == "2":
            productos_stock_bajo(cur)
        elif opcion == "3":
            modificar_precio(cur)
        elif opcion == "4":
            proponer_producto(cur)
        elif opcion == "0":
            print("👋 Cerrando sesión repositor.")
            break
        else:
            print("❌ Opción inválida.")

def ingresar_stock(cur):
    print("\n📥 INGRESO DE STOCK")
    entrada = input("Presioná Enter para escanear o escribí nombre/código: ").strip().lower()
    if not entrada:
        codigo = obtener_codigo_barra()
        if not codigo:
            print("⚠️ No se obtuvo ningún código.")
            return
    else:
        codigo = entrada

    cur.execute("""
        SELECT id, nombre, stock_actual FROM productos
        WHERE LOWER(nombre) LIKE %s OR codigo_barra LIKE %s;
    """, (f"%{codigo}%", f"%{codigo}%"))
    productos = cur.fetchall()

    if not productos:
        print("❌ Producto no encontrado.")
        return

    for i, (pid, nombre, stock) in enumerate(productos):
        print(f"[{i}] {nombre} | Stock actual: {stock}")

    try:
        idx = int(input("Elegí el número de producto: ").strip())
        pid, nombre, stock = productos[idx]
    except (ValueError, IndexError):
        print("❌ Selección inválida.")
        return

    try:
        cantidad = int(input(f"Ingresar cantidad a sumar para '{nombre}': "))
        if cantidad < 1:
            print("⚠️ Cantidad inválida.")
            return
    except ValueError:
        print("❌ Número inválido.")
        return

    cur.execute("""
        UPDATE productos
        SET stock_actual = stock_actual + %s
        WHERE id = %s;
    """, (cantidad, pid))
    cur.connection.commit()
    print(f"✅ Se sumaron {cantidad} unidades a '{nombre}'.")

def productos_stock_bajo(cur):
    print("\n📉 Productos con stock por debajo del mínimo:")
    cur.execute("""
        SELECT nombre, codigo_barra, stock_actual, stock_minimo
        FROM productos
        WHERE stock_actual < stock_minimo
        ORDER BY nombre;
    """)
    resultados = cur.fetchall()

    if not resultados:
        print("✅ No hay productos con stock bajo.")
        return

    print(f"\n{'Producto':<30} | {'Código':<15} | {'Stock':>5} / Mínimo")
    print("-" * 60)
    for nombre, codigo, stock, minimo in resultados:
        print(f"{nombre:<30} | {codigo:<15} | {stock:>5} / {minimo}")


def modificar_precio(cur):
    print("\n📉 MODIFICAR PRECIO")
    entrada = input("Presioná Enter para escanear o escribí nombre/código: ").strip().lower()
    if not entrada:
        codigo = obtener_codigo_barra()
        if not codigo:
            print("⚠️ No se obtuvo ningún código.")
            return
    else:
        codigo = entrada

    cur.execute("""
        SELECT id, nombre, precio_venta FROM productos
        WHERE LOWER(nombre) LIKE %s OR codigo_barra LIKE %s;
    """, (f"%{codigo}%", f"%{codigo}%"))
    productos = cur.fetchall()

    if not productos:
        print("❌ Producto no encontrado.")
        return

    for i, (pid, nombre, precio) in enumerate(productos):
        print(f"[{i}] {nombre} | Precio actual: ${precio:.2f}")

    try:
        idx = int(input("Elegí el producto a modificar: ").strip())
        pid, nombre, precio = productos[idx]
    except (ValueError, IndexError):
        print("❌ Selección inválida.")
        return

    try:
        nuevo = float(input("Nuevo precio: "))
        if nuevo <= 0:
            print("⚠️ Debe ser mayor a 0.")
            return
    except ValueError:
        print("❌ Número inválido.")
        return

    cur.execute("UPDATE productos SET precio_venta = %s WHERE id = %s;", (nuevo, pid))
    cur.connection.commit()
    print(f"✅ Precio de '{nombre}' actualizado a ${nuevo:.2f}")

def proponer_producto(cur):
    print("\n📦 Propuesta de nuevo producto")

    nombre = input("Nombre del producto: ").strip()
    if not nombre:
        print("❌ Nombre obligatorio.")
        return

    id_categoria = seleccionar_categoria(cur)
    if not id_categoria:
        print("❌ No se seleccionó ninguna categoría.")
        return

    try:
        precio_venta = float(input("💰 Precio de venta: "))
        stock = int(input("📦 Stock inicial: "))
        stock_min = int(input("🔻 Stock mínimo: "))
    except ValueError:
        print("❌ Valor numérico inválido.")
        return

    compra_raw = input("💸 Precio de compra (opcional): ").strip()
    precio_compra = float(compra_raw) if compra_raw else None

    gen = GeneradorEAN13(cur)
    codigo_barra = gen.generar_codigo_unico()
    print(f"🧾 Código de barras generado: {codigo_barra}")

    foto_bytes = capturar_foto(nombre)
    if not foto_bytes:
        print("🚫 No se capturó la imagen.")
        return

    cur.execute("""
        INSERT INTO productos (
            nombre, precio_venta, precio_compra,
            stock_actual, stock_minimo,
            codigo_barra, foto, categoria_id,
            activo
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE);
    """, (
        nombre, precio_venta, precio_compra,
        stock, stock_min,
        codigo_barra, foto_bytes, id_categoria
    ))
    cur.connection.commit()

    print("\n✅ Producto propuesto con éxito. Quedará pendiente de aprobación por el dueño o gerente.")


def menu_gerente(cur):
    while True:
        print("\n👔 MENÚ GERENTE")
        print("[1] Aprobar productos propuestos")
        print("[2] Consultar productos inactivos")
        print("[3] Ver productos con stock bajo")
        print("[4] Modificar precios")
        print("[0] Cerrar sesión")

        opcion = input("Elegí una opción: ").strip()

        if opcion == "1":
            revisar_productos_pendientes(cur)
        elif opcion == "2":
            listar_inactivos(cur)
        elif opcion == "3":
            productos_stock_bajo(cur)
        elif opcion == "4":
            modificar_precio(cur)
        elif opcion == "0":
            print("👋 Cerrando sesión gerente.")
            break
        else:
            print("❌ Opción inválida.")

def listar_inactivos(cur):
    cur.execute("""
        SELECT id, nombre, codigo_barra, precio_venta
        FROM productos
        WHERE activo = FALSE
        ORDER BY nombre;
    """)
    inactivos = cur.fetchall()

    if not inactivos:
        print("✅ No hay productos inactivos.")
        return

    print(f"\n{'ID':<4} {'Nombre':<30} {'Código':<15} {'Precio':>8}")
    print("-" * 60)
    for pid, nombre, codigo, precio in inactivos:
        print(f"{pid:<4} {nombre:<30} {codigo:<15} ${precio:>7.2f}")

def revisar_productos_pendientes(cur):
    print("\n🧾 Productos pendientes de aprobación:")

    cur.execute("""
        SELECT id, nombre, descripcion, precio_venta, precio_compra,
               stock_actual, codigo_barra, foto
        FROM productos
        WHERE activo = FALSE
        ORDER BY id;
    """)
    productos = cur.fetchall()

    if not productos:
        print("✅ No hay productos para revisar.")
        return

    for fila in productos:
        pid, nombre, descripcion, precio_venta, precio_compra, stock, codigo, foto = fila

        print("\n" + "=" * 50)
        print(f"🆔 ID: {pid}")
        print(f"📦 Nombre: {nombre}")
        print(f"🧾 Descripción: {descripcion or '[sin descripción]'}")
        print(f"💲 Precio de venta: ${precio_venta:.2f}")
        if precio_compra:
            print(f"💸 Precio de compra: ${precio_compra:.2f}")
        print(f"📦 Stock inicial: {stock}")
        print(f"🏷️ Código de barras: {codigo}")

        # Mostrar imagen si existe (abrir con visor del sistema)
        if foto:
            try:
                img = Image.open(BytesIO(foto))
                img.show(title=f"Producto: {nombre}")
            except Exception as e:
                print(f"⚠️ No se pudo mostrar la imagen: {e}")
        else:
            print("⚠️ Sin imagen asociada.")

        print("\n¿Qué hacer?")
        print("[A] Aprobar tal cual")
        print("[M] Modificar y aprobar")
        print("[Enter] Omitir")

        op = input("Opción: ").strip().lower()

        if op == "a":
            cur.execute("UPDATE productos SET activo = TRUE WHERE id = %s;", (pid,))
            print("✅ Producto aprobado.")
        elif op == "m":
            nuevo_nombre = input("✏️ Nuevo nombre (Enter para mantener): ").strip() or nombre
            nuevo_precio = input("💲 Nuevo precio de venta (Enter para mantener): ").strip()
            nuevo_precio = float(nuevo_precio) if nuevo_precio else precio_venta
            nueva_desc = input("📝 Descripción (Enter para mantener): ").strip() or descripcion or ""

            modificar_foto = input("🖼️ ¿Querés cambiar la foto? [s/N]: ").strip().lower() == "s"
            nueva_foto = capturar_foto(nuevo_nombre) if modificar_foto else foto

            cur.execute("""
                UPDATE productos
                SET nombre = %s,
                    precio_venta = %s,
                    descripcion = %s,
                    foto = %s,
                    activo = TRUE
                WHERE id = %s;
            """, (nuevo_nombre, nuevo_precio, nueva_desc, nueva_foto, pid))
            print("✅ Producto modificado y aprobado.")
        else:
            print("⏭️ Producto omitido.")

    cur.connection.commit()
    print("\n✔️ Revisión completada.")