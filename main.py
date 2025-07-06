from bbdd.db_config import conectar_db
from modulos.main_router import MainRouter

def main():
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo = TRUE;")
    tiene_usuarios = cur.fetchone()[0] > 0

    router = MainRouter()
    if not tiene_usuarios:
        router.iniciar_con_setup()

if __name__ == "__main__":
    main()
