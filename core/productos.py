from bbdd import db_config
import random

def buscar_productos(filtro: str = "") -> list[dict]:
    
    conn = db_config.conectar_db()
    cur = conn.cursor()

    if filtro:
        cur.execute("""
            SELECT nombre, codigo, stock, precio_venta, activo
            FROM productos
            WHERE LOWER(nombre) LIKE %s OR LOWER(codigo) LIKE %s
            ORDER BY nombre
        """, (f"%{filtro.lower()}%", f"%{filtro.lower()}%"))
    else:
        cur.execute("""
            SELECT nombre, codigo, stock, precio_venta, activo
            FROM productos
            ORDER BY nombre
        """)

    productos = [
        {
            "nombre": fila[0],
            "codigo": fila[1],
            "stock": fila[2],
            "precio_venta": fila[3],
            "activo": fila[4]
        }
        for fila in cur.fetchall()
    ]
    conn.close()
    return productos

def modificar_stock(codigo: str, nuevo_stock: int) -> bool:
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()

        cur.execute("""
            UPDATE productos
            SET stock = %s
            WHERE codigo = %s
        """, (nuevo_stock, codigo))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al actualizar stock: {e}")
        return False
    
def actualizar_precios(codigo: str, precio_compra: float, precio_venta: float) -> bool:
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()

        cur.execute("""
            UPDATE productos
            SET precio_compra = %s,
                precio_venta = %s
            WHERE codigo = %s
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
        cur.execute("UPDATE productos SET activo = FALSE WHERE codigo = %s", (codigo,))
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
        cur.execute("UPDATE productos SET activo = TRUE WHERE codigo = %s", (codigo,))
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
            SELECT nombre, codigo, descripcion, categoria, stock,
                   precio_compra, precio_venta, activo, foto
            FROM productos
            WHERE codigo = %s
        """, (codigo,))

        fila = cur.fetchone()
        conn.close()

        if fila:
            return {
                "nombre": fila[0],
                "codigo": fila[1],
                "descripcion": fila[2],
                "categoria": fila[3],
                "stock": fila[4],
                "precio_compra": float(fila[5]),
                "precio_venta": float(fila[6]),
                "activo": fila[7],
                "foto": fila[8]
            }
        return None
    except Exception as e:
        print(f"Error al obtener producto: {e}")
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
                     stock_minimo: int | None, foto_bytes: bytes | None = None) -> bool:
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

        # Armar UPDATE dinámico
        consulta = """
            UPDATE productos SET
                nombre = %s,
                descripcion = %s,
                categoria_id = %s,
                precio_venta = %s,
                precio_compra = %s,
                stock_minimo = %s,
                estado = 'activo'
        """
        valores = [nombre, descripcion, categoria_id, precio_venta, precio_compra, stock_minimo]

        if foto_bytes:
            consulta += ", foto = %s"
            valores.append(foto_bytes)

        consulta += " WHERE codigo_barra = %s"
        valores.append(codigo)

        cur.execute(consulta, tuple(valores))
        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error al aprobar producto: {e}")
        return False

def obtener_pendientes_de_aprobacion() -> list[dict]:
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT nombre, codigo_barra, stock_actual, fecha_creacion
            FROM productos
            WHERE estado = 'pendiente'
            ORDER BY fecha_creacion ASC
        """)
        filas = cur.fetchall()
        conn.close()

        return [
            {
                "nombre": f[0],
                "codigo_barra": f[1],
                "stock_actual": f[2],
                "fecha_creacion": f[3]
            }
            for f in filas
        ]

    except Exception as e:
        print(f"Error al obtener productos pendientes: {e}")
        return []
