from PySide6.QtWidgets import QApplication
from bbdd.db_config import conectar_db
from login_window import LoginWindow
from modulos import setup_inicial
import sys

def main():
    app = QApplication(sys.argv)

    conn = conectar_db()
    cur = conn.cursor()

    # ¿Ya existen usuarios activos?
    cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo = TRUE;")
    tiene_usuarios = cur.fetchone()[0] > 0

    if tiene_usuarios:
        ventana = LoginWindow()
    else:
        ventana = setup_inicial.SetupInicialDialog()

    ventana.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()