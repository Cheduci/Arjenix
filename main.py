from bbdd.db_config import conectar_db, ejecutar_schema_si_necesario
from modulos.main_router import MainRouter

def main():
    conn = conectar_db()
    cur = conn.cursor()
    ejecutar_schema_si_necesario(cur)
    cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo = TRUE;")
    tiene_usuarios = cur.fetchone()[0] > 0

    if not tiene_usuarios:
        MainRouter(arranca_con_setup=True)
    else:
        MainRouter()


if __name__ == "__main__":
    main()
