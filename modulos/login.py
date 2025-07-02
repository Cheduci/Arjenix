import bcrypt
from datetime import datetime

def iniciar_sesion(cur):
    print("\n🔐 Inicio de sesión")
    username = input("Nombre de usuario: ").strip()
    password = input("Contraseña: ").strip()

    cur.execute("""
        SELECT u.id, u.password_hash, u.activo, u.debe_cambiar_password,
               u.persona_id, r.nombre AS rol
        FROM usuarios u
        JOIN roles r ON u.rol_id = r.id
        WHERE u.username = %s;
    """, (username,))
    fila = cur.fetchone()

    if not fila:
        print("❌ Usuario no encontrado.")
        return None

    uid, hash_db, activo, cambio_requerido, persona_id, rol = fila

    if not activo:
        print("⛔ Usuario inactivo.")
        return None

    if not bcrypt.checkpw(password.encode(), hash_db.encode()):
        print("❌ Contraseña incorrecta.")
        return None

    # Actualizar último login
    cur.execute("UPDATE usuarios SET ultimo_login = %s WHERE id = %s;", (datetime.now(), uid))
    cur.connection.commit()

    print(f"✅ Bienvenido, {username} ({rol})")

    # Devolver sesión activa
    return {
        "id": uid,
        "persona_id": persona_id,
        "rol": rol,
        "debe_cambiar_password": cambio_requerido,
        "username": username
    }