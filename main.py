from bbdd.db_config import conectar_db
from modulos.main_router import MainRouter
from PySide6.QtWidgets import QMessageBox, QApplication
from psycopg import OperationalError
import sys

def main():
    app = QApplication(sys.argv)
    try:
        conn = conectar_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo = TRUE;")
        tiene_usuarios = cur.fetchone()[0] > 0

        router = MainRouter(arranca_con_setup=not tiene_usuarios)
        sys.exit(app.exec())

    
    except ConnectionError as e:
        QMessageBox.critical(None, "Error de conexión", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
