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

def obtener_configuracion_sistema() -> dict:
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("SELECT clave, valor FROM configuracion_sistema")
    config = {clave: valor for clave, valor in cur.fetchall()}
    cur.close()
    return config

def guardar_configuracion_sistema(config: dict):
    conn = conectar_db()
    cur = conn.cursor()
    for clave, valor in config.items():
        cur.execute("""
            INSERT INTO configuracion_sistema (clave, valor)
            VALUES (%s, %s)
            ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor
        """, (clave, valor))
    conn.commit()
    cur.close()