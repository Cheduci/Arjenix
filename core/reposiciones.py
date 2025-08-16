from bbdd import db_config

def registrar_reposicion(codigo_barra: str, cantidad: int, usuario_id: int | None = None, motivo: str = None) -> bool:
    try:
        conn = db_config.conectar_db()
        cur = conn.cursor()

        # Obtener producto_id
        cur.execute("SELECT id FROM productos WHERE codigo_barra = %s", (codigo_barra,))
        resultado = cur.fetchone()
        if not resultado:
            return False
        producto_id = resultado[0]

        # Insertar reposición
        cur.execute("""
            INSERT INTO reposiciones (producto_id, cantidad, usuario_id, motivo)
            VALUES (%s, %s, %s, %s)
        """, (producto_id, cantidad, usuario_id, motivo))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error al registrar reposición: {e}")
        return False
    finally:
        if conn:
            conn.close()
