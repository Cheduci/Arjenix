import bcrypt
from bbdd import db_config
from PySide6.QtWidgets import QMessageBox

def autenticar_usuario(usuario, password):
    
    try:
        conn = db_config.conectar_db()
    except ConnectionError as e:
        QMessageBox.critical(None, "Error de conexión", str(e))
        return None

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.username, u.password_hash, u.debe_cambiar_password,
                r.nombre AS rol, p.nombre
            FROM usuarios u
            JOIN personas p ON u.persona_id = p.id
            JOIN roles r ON u.rol_id = r.id
            WHERE u.username = %s AND u.activo = TRUE
        """, (usuario,))
        fila = cur.fetchone()
        conn.close()

        if not fila:
            return None

        if not bcrypt.checkpw(password.encode(), fila[2].encode()):
            return None

        return {
            "id": fila[0],
            "username": fila[1],
            "debe_cambiar_password": fila[3],
            "rol": fila[4],
            "nombre": fila[5]
        }
    except ConnectionError:
        return "error_conexion"
    except Exception as e:
        return None