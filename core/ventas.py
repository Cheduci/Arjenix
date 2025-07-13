from bbdd.db_config import conectar_db
from datetime import datetime

def registrar_venta(sesion, productos: list[dict], metodo_pago: str) -> bool:
    try:
        conn = conectar_db()
        cur = conn.cursor()
        usuario = sesion["username"]
        total = sum(p["cantidad"] * p["precio_unitario"] for p in productos)

        # Insertar encabezado
        cur.execute(
            "INSERT INTO ventas (fecha_hora, total, metodo_pago, usuario) VALUES (%s, %s, %s, %s) RETURNING id",
            (datetime.now(), total, metodo_pago, usuario)
        )
        venta_id = cur.fetchone()[0]

        for p in productos:
            # Obtener ID del producto
            cur.execute("SELECT id FROM productos WHERE codigo_barra = %s", (p["codigo"],))
            fila = cur.fetchone()
            if not fila:
                raise Exception(f"Producto no encontrado: {p['codigo']}")

            prod_id = fila[0]
            precio_compra = p.get("precio_compra")

            # Insertar detalle
            cur.execute("""
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, precio_compra)
                VALUES (%s, %s, %s, %s, %s)
            """, (venta_id, prod_id, p["cantidad"], p["precio_unitario"], precio_compra))

            # Actualizar stock
            cur.execute("""
                UPDATE productos
                SET stock_actual = stock_actual - %s
                WHERE id = %s
            """, (p["cantidad"], prod_id))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error en registrar_venta: {e}")
        return False
