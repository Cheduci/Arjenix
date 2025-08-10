from bbdd import db_config
import random

def buscar_productos(nombre: str = "", codigo: str = "", categoria: str | None = None):
    conn = db_config.conectar_db()
    cur = conn.cursor()

    consulta = """
        SELECT p.nombre, p.codigo_barra, c.nombre AS categoria, p.stock_actual, p.precio_venta, p.estado
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        WHERE 1=1
    """
    valores = []

    if nombre:
        consulta += " AND LOWER(p.nombre) LIKE %s"
        valores.append(f"%{nombre}%")

    if codigo:
        consulta += " AND p.codigo_barra ILIKE %s"
        valores.append(f"%{codigo}%")

    if categoria:
        consulta += " AND c.nombre = %s"
        valores.append(categoria)

    cur.execute(consulta, tuple(valores))
    filas = cur.fetchall()
    conn.close()

    return [
        {
            "nombre": f[0],
            "codigo_barra": f[1],
            "categoria": f[2] or "Sin categoría",
            "stock_actual": f[3],
            "precio_venta": f[4],
            "estado": f[5]
        } for f in filas
    ]


def modificar_stock(codigo: str, nuevo_stock: int, stock_minimo=None) -> bool:
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()

        if stock_minimo is not None:
            cur.execute("""
                UPDATE productos
                SET stock_actual = %s, stock_minimo = %s
                WHERE codigo_barra = %s
            """, (nuevo_stock, stock_minimo, codigo))
        else:
            cur.execute("""
                UPDATE productos
                SET stock_actual = %s
                WHERE codigo_barra = %s
            """, (nuevo_stock, codigo))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al actualizar stock: {e}")
        return False

def obtener_stock_actual(codigo: str) -> int:
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()

        cur.execute("SELECT stock_actual FROM productos WHERE codigo_barra = %s", (codigo,))
        resultado = cur.fetchone()
        conn.close()
        return resultado[0] if resultado else 0
    except Exception as e:
        print(f"Error al consultar stock: {e}")
        return 0

    
def actualizar_precios(codigo: str, precio_compra: float, precio_venta: float) -> bool:
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()

        cur.execute("""
            UPDATE productos
            SET precio_compra = %s,
                precio_venta = %s
            WHERE codigo_barra = %s
        """, (precio_compra, precio_venta, codigo))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al actualizar precios: {e}")
        return False

def inactivar_producto(codigo: str) -> bool:
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()
        cur.execute("UPDATE productos SET estado = 'inactivo' WHERE codigo_barra = %s", (codigo,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al inactivar producto: {e}")
        return False

def reactivar_producto(codigo: str) -> bool:
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()
        cur.execute("UPDATE productos SET estado = 'activo' WHERE codigo_barra = %s", (codigo,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al reactivar producto: {e}")
        return False

def obtener_producto_por_codigo(codigo: str) -> dict | None:
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                p.id,
                p.nombre,
                p.codigo_barra,
                COALESCE(p.descripcion, ''),
                COALESCE(c.nombre, 'Sin categoría'),
                COALESCE(p.stock_actual, 0),
                COALESCE(p.stock_minimo, 0),
                COALESCE(p.precio_compra, 0),
                COALESCE(p.precio_venta, 0),
                COALESCE(p.estado, 'pendiente'),
                p.foto  -- si es BYTEA, dejala sin COALESCE
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.codigo_barra = %s
        """, (codigo,))

        fila = cur.fetchone()
        conn.close()

        if fila:
            return {
                "id": fila[0],
                "nombre": fila[1],
                "codigo_barra": fila[2],
                "descripcion": fila[3],
                "categoria": fila[4],
                "stock_actual": fila[5],
                "stock_minimo": fila[6],
                "precio_compra": float(fila[7]),
                "precio_venta": float(fila[8]),
                "estado": fila[9],
                "foto": fila[10]
            }
        return None
    except Exception as e:
        raise RuntimeError(f"No se pudo obtener el producto: {e}")
    finally:
        cur.close()

def obtener_producto_por_id(id):
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                p.id,
                p.nombre,
                p.codigo_barra,
                COALESCE(p.descripcion, ''),
                COALESCE(c.nombre, 'Sin categoría'),
                COALESCE(p.stock_actual, 0),
                COALESCE(p.stock_minimo, 0),
                COALESCE(p.precio_compra, 0),
                COALESCE(p.precio_venta, 0),
                COALESCE(p.estado, 'pendiente'),
                p.foto  -- si es BYTEA, dejala sin COALESCE
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.id = %s
        """, (id,))

        fila = cur.fetchone()
        conn.close()

        if fila:
            return {
                "id": fila[0],
                "nombre": fila[1],
                "codigo_barra": fila[2],
                "descripcion": fila[3],
                "categoria": fila[4],
                "stock_actual": fila[5],
                "stock_minimo": fila[6],
                "precio_compra": float(fila[7]),
                "precio_venta": float(fila[8]),
                "estado": fila[9],
                "foto": fila[10]
            }
        return None
    except Exception as e:
        raise RuntimeError(f"No se pudo obtener el producto: {e}")
    finally:
        cur.close()

def obtener_basico_por_codigo(codigo: str) -> dict | None:
    """
    Retorna los campos mínimos de un producto: nombre, código, stock, fecha de creación.
    Ideal para listas o etapas previas a la aprobación.
    """
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT nombre, codigo_barra, stock_actual, fecha_creacion
            FROM productos
            WHERE codigo_barra = %s
        """, (codigo,))
        
        fila = cur.fetchone()
        conn.close()

        if fila:
            return {
                "nombre": fila[0],
                "codigo_barra": fila[1],
                "stock_actual": fila[2],
                "fecha_creacion": fila[3]
            }
        return None

    except Exception as e:
        print(f"Error al obtener producto básico: {e}")
        return None

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
def aprobar_producto(codigo: str, nombre: str, descripcion: str, categoria: str,
                     precio_venta: float, precio_compra: float | None,
                     stock_minimo: int | None, item_id: int, foto_bytes: bytes | None = None) -> bool:
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()

        # Obtener ID de categoría (crear si no existe)
        cur.execute("SELECT id FROM categorias WHERE nombre = %s", (categoria,))
        fila = cur.fetchone()
        if fila:
            categoria_id = fila[0]
        else:
            cur.execute("INSERT INTO categorias (nombre) VALUES (%s) RETURNING id", (categoria,))
            categoria_id = cur.fetchone()[0]

        # 💰 Validación de precios
        if precio_compra is not None and precio_venta < precio_compra:
            return False, "❌ El precio de venta no puede ser menor que el de compra."

        # Armar UPDATE dinámico
        columnas = [
            "nombre = %s",
            "codigo_barra = %s",
            "descripcion = %s",
            "categoria_id = %s",
            "precio_venta = %s",
            "precio_compra = %s",
            "stock_minimo = %s",
            "estado = 'activo'"
        ]
        valores = [nombre, codigo, descripcion, categoria_id, precio_venta, precio_compra, stock_minimo]

        if foto_bytes is not None:
            columnas.append("foto = %s")
            valores.append(foto_bytes)

        valores.append(item_id)

        consulta = f"""
            UPDATE productos SET
                {', '.join(columnas)}
            WHERE id = %s
        """

        cur.execute(consulta, tuple(valores))
        conn.commit()
        conn.close()
        return True, None

    except Exception as e:
        return False, f"❌ Error al aprobar producto: {e}"

def obtener_pendientes_de_aprobacion() -> list[dict]:
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, nombre, codigo_barra, stock_actual, fecha_creacion
            FROM productos
            WHERE estado = 'pendiente'
            ORDER BY fecha_creacion ASC
        """)
        filas = cur.fetchall()
        conn.close()

        return [
            {
                "id": f[0],
                "nombre": f[1],
                "codigo_barra": f[2],
                "stock_actual": f[3],
                "fecha_creacion": f[4]
            }
            for f in filas
        ]

    except Exception as e:
        print(f"Error al obtener productos pendientes: {e}")
        return []

def crear_categoria(nombre: str):
    conn = db_config.conectar_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO categorias (nombre) VALUES (%s) ON CONFLICT DO NOTHING;", (nombre.capitalize(),))
    conn.commit()
    conn.close()

def listar_categorias() -> list[str]:
    conn = db_config.conectar_db()
    cur = conn.cursor()
    cur.execute("SELECT nombre FROM categorias ORDER BY nombre;")
    categorias = [row[0] for row in cur.fetchall()]
    conn.close()
    return categorias

def eliminar_categoria(nombre: str) -> bool:
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM categorias WHERE nombre = %s;", (nombre,))
        exito = cur.rowcount > 0
        conn.commit()
        conn.close()
        return exito
    except Exception:
        return False

def renombrar_categoria(nombre_actual: str, nuevo_nombre: str):
    conn = db_config.conectar_db()
    cur = conn.cursor()
    cur.execute("UPDATE categorias SET nombre = %s WHERE nombre = %s;", (nuevo_nombre, nombre_actual))
    conn.commit()
    conn.close()

def categoria_en_uso(nombre: str) -> bool:
    conn = db_config.conectar_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM productos
        WHERE categoria_id = (SELECT id FROM categorias WHERE nombre = %s)
        LIMIT 1;
    """, (nombre,))
    en_uso = cur.fetchone() is not None
    conn.close()
    return en_uso

def ranking_ventas():
    conn = db_config.conectar_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.nombre, p.codigo_barra,
               SUM(d.cantidad) AS cantidad_vendida,
               SUM(d.cantidad * d.precio_unitario) AS total_recaudado
        FROM detalle_ventas d
        JOIN productos p ON d.codigo_producto = p.codigo_barra
        GROUP BY p.nombre, p.codigo_barra
        ORDER BY cantidad_vendida DESC
        LIMIT 10
    """)
    filas = cur.fetchall()
    conn.close()
    return [
        {
            "nombre": f[0],
            "codigo_barra": f[1],
            "cantidad_vendida": f[2],
            "total_recaudado": f[3]
        } for f in filas
    ]

def actualizar_foto(codigo: str, foto_bytes: bytes) -> bool:
    """Actualiza la foto de un producto en la base de datos."""
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()
        cur.execute(
            "UPDATE productos SET foto = %s WHERE codigo_barra = %s",
            (foto_bytes, codigo)
        )
        conn.commit()
        exito = cur.rowcount > 0
        conn.close()
        return exito
    except Exception as e:
        print(f"Error al actualizar foto: {e}")
        return False

class ErrorStockBajo(Exception):
    pass

def obtener_productos_con_stock_bajo(self, umbral=None):
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()
        
        # Si no se define un umbral externo, usar el stock_minimo de cada producto
        if umbral is None:
            cur.execute("""
                SELECT nombre, codigo_barra, stock_minimo, stock_actual, proveedor
                FROM productos
                WHERE stock_minimo IS NOT NULL AND stock_actual <= stock_minimo
                ORDER BY nombre ASC
            """)
        else:
            cur.execute("""
                SELECT nombre, codigo_barra, stock_minimo, stock_actual, proveedor
                FROM productos
                WHERE stock_actual <= %s
                ORDER BY nombre ASC
            """, (umbral,))
        
        resultados = cur.fetchall()
        cur.close()

        return [
            {
                "nombre": fila[0],
                "codigo_barra": fila[1],
                "stock_minimo": fila[2],
                "stock_actual": fila[3],
                "proveedor": fila[4] or ""
            }
            for fila in resultados
        ]
    
    except Exception as e:
        raise ErrorStockBajo(f"No se pudo obtener productos con stock bajo: {e}")
    
    finally:
        if conn:
            conn.close()

def guardar_codigo(codigo,id_producto):
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()
        cur.execute("UPDATE productos SET codigo_barra = %s WHERE id = %s", (codigo, id_producto))
        conn.commit()
        conn.close()
        return True, None
    except Exception as e:
        print(f"Error al guardar código: {e}")
        return False, str(e)
    finally:
        if conn:
            conn.close()