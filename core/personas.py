from bbdd.db_config import conectar_db

def hay_personas_disponibles() -> bool:
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM personas
        WHERE id NOT IN (SELECT persona_id FROM usuarios WHERE persona_id IS NOT NULL)
        LIMIT 1
    """)
    resultado = cur.fetchone()
    conn.close()
    return bool(resultado)

def obtener_personas_sin_usuario():
    cur = conectar_db().cursor()
    cur.execute("""
        SELECT id, nombre, apellido, dni
        FROM personas
        WHERE id NOT IN (SELECT persona_id FROM usuarios WHERE persona_id IS NOT NULL)
        ORDER BY apellido, nombre
    """)
    return [
        {"id": r[0], "nombre": r[1], "apellido": r[2], "dni": r[3]}
        for r in cur.fetchall()
    ]

def dni_existe(dni: str) -> bool:
    cur = conectar_db().cursor()
    cur.execute("SELECT 1 FROM personas WHERE dni = %s", (dni,))
    return bool(cur.fetchone())

def insertar_persona(datos: dict) -> int | None:
    """
    Inserta una nueva persona y retorna su ID.
    `datos` debe contener: dni, nombre, apellido, email, fecha_nacimiento
    """
    try:
        conn = conectar_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO personas (dni, nombre, apellido, email, fecha_nacimiento, activo)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            RETURNING id
        """, (
            datos["dni"],
            datos["nombre"],
            datos["apellido"],
            datos.get("email"),
            datos["fecha_nacimiento"]
        ))

        persona_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        return persona_id

    except Exception as e:
        print(f"❌ Error al insertar persona: {e}")
        return None
