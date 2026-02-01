# config_setup.py
import os, sys, configparser
from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
CONFIG_PATH = os.path.join(base_dir, "bbdd", "arjenix_config.ini")
DB_NAME = "arjenix"

class ConfigDialog(QDialog):
    def __init__(self, valores=None):
        super().__init__()
        self.setWindowTitle("Configuración de conexión a PostgreSQL")
        layout = QFormLayout(self)

        self.host = QLineEdit(valores.get("host", ""))
        self.port = QLineEdit(valores.get("port", "5432"))
        self.user = QLineEdit(valores.get("user", ""))
        self.password = QLineEdit(valores.get("password", ""))
        self.password.setEchoMode(QLineEdit.Password)

        layout.addRow("Host:", self.host)
        layout.addRow("Puerto:", self.port)
        layout.addRow("Usuario:", self.user)
        layout.addRow("Contraseña:", self.password)

        btn_guardar = QPushButton("Guardar")
        btn_guardar.clicked.connect(self.accept)
        layout.addRow(btn_guardar)

    def obtener_datos(self):
        return {
            "name": DB_NAME,
            "host": self.host.text(),
            "port": self.port.text(),
            "user": self.user.text(),
            "password": self.password.text()
        }

def asegurar_configuracion():
    config = configparser.ConfigParser()

    # Paso 1: si no existe, crear archivo con sección [DB] vacía
    if not os.path.isfile(CONFIG_PATH):
        config["DB"] = {
            "name": DB_NAME,
            "user": "",
            "password": "",
            "host": "",
            "port": ""
        }
        with open(CONFIG_PATH, "w") as f:
            config.write(f)

    # Paso 2: leer archivo
    config.read(CONFIG_PATH)

    # Paso 3: si no existe la sección [DB], agregarla
    if "DB" not in config:
        config["DB"] = {
            "name": DB_NAME,
            "user": "",
            "password": "",
            "host": "",
            "port": ""
        }
        with open(CONFIG_PATH, "w") as f:
            config.write(f)

    db = config["DB"]

    # Paso 4: si faltan campos, mostrar formulario
    if not all([db.get("user"), db.get("password"), db.get("host"), db.get("port")]):
        dlg = ConfigDialog(db)
        if dlg.exec():
            nuevos = dlg.obtener_datos()
            config["DB"] = nuevos
            with open(CONFIG_PATH, "w") as f:
                config.write(f)
        else:
            sys.exit(0)

    return dict(config["DB"])
