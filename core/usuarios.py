from bbdd.db_config import conectar_db

def crear_usuario(persona_id, username, password_hash, rol_id) -> bool:
    try:
        conn = conectar_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO usuarios (persona_id, username, password_hash, rol_id)
            VALUES (%s, %s, %s, %s)
        """, (persona_id, username, password_hash, rol_id))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
        return False


def username_existe(username: str) -> bool:
    cur = conectar_db().cursor()
    cur.execute("SELECT 1 FROM usuarios WHERE username = %s", (username,))
    return bool(cur.fetchone())
