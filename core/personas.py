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

def dni_existe(dni: str, ignorar_id: int | None = None) -> bool:
    conn = conectar_db()
    cur = conn.cursor()

    if ignorar_id is not None:
        cur.execute(
            "SELECT 1 FROM personas WHERE dni = %s AND id <> %s",
            (dni, ignorar_id)
        )
    else:
        cur.execute(
            "SELECT 1 FROM personas WHERE dni = %s",
            (dni,)
        )

    existe = bool(cur.fetchone())
    conn.close()
    return existe


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
        return persona_id, None

    except Exception as e:
        return None, str(e)

def obtener_personas_desde_db():
    """
    Obtiene una lista de todas las personas activas.
    Retorna una lista de diccionarios con los campos: id, dni, nombre, apellido, email, fecha_nacimiento.
    """
    cur = conectar_db().cursor()
    cur.execute("""
        SELECT id, dni, nombre, apellido, email, fecha_nacimiento, foto
        FROM personas
        ORDER BY apellido, nombre
    """)
    return [
        {
            "id": r[0],
            "dni": r[1],
            "nombre": r[2],
            "apellido": r[3],
            "email": r[4],
            "fecha_nacimiento": r[5],
            "foto": r[6]
        }
        for r in cur.fetchall()
    ]

def actualizar_persona(datos: dict) -> tuple[bool, str | None]:
    """
    Actualiza los datos de una persona. `datos` debe contener: id, dni, nombre, apellido, email, fecha_nacimiento
    Retorna True si fue exitoso, o un string con el error.
    """
    try:
        # Verificar si el nuevo DNI ya existe en otro registro
        if dni_existe(datos["dni"], ignorar_id=datos["id"]):
            return "Ya existe otra persona registrada con ese DNI."

        conn = conectar_db()
        cur = conn.cursor()

        # Actualizar los datos
        cur.execute("""
            UPDATE personas
            SET dni = %s,
                nombre = %s,
                apellido = %s,
                email = %s,
                fecha_nacimiento = %s
            WHERE id = %s
        """, (
            datos["dni"],
            datos["nombre"],
            datos["apellido"],
            datos.get("email"),
            datos["fecha_nacimiento"],
            datos["id"]
        ))

        conn.commit()
        conn.close()
        return True, None

    except Exception as e:
        return False, str(e)

def eliminar_persona_por_id(id_persona):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM personas WHERE id = %s", (id_persona,))

        if cursor.rowcount == 0:
            raise ValueError(f"No se encontró ninguna persona con ID {id_persona}")

        conn.commit()
        return True, None  # opcional: señal de éxito

    except Exception as e:
        return False, str(e)  # opcional: señal de error

    finally:
        if 'conn' in locals():
            conn.close()

def actualizar_foto_persona(persona_id: int, foto_bytes: bytes):
    try:
        conn = conectar_db()
        cur = conn.cursor()
        if foto_bytes is not None:
            cur.execute("""
                UPDATE personas
                SET foto = %s
                WHERE id = %s;
            """, (foto_bytes, persona_id))
        else:
            cur.execute("""
                UPDATE personas
                SET foto = NULL
                WHERE id = %s;
            """, (persona_id,))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        if 'conn' in locals():
            conn.close()
