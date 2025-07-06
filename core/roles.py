from bbdd.db_config import conectar_db

def obtener_roles() -> list[tuple[int, str]]:
    cur = conectar_db().cursor()
    cur.execute("SELECT id, nombre FROM roles ORDER BY nombre")
    return cur.fetchall()
