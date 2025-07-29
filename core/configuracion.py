from bbdd.db_config import conectar_db


def obtener_config_empresa():
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("SELECT nombre, slogan, logo FROM configuracion_empresa LIMIT 1")
    datos = cur.fetchone()
    cur.close()

    if datos:
        return {
            "nombre": datos[0],
            "slogan": datos[1],
            "logo": datos[2]
        }
    return {}
