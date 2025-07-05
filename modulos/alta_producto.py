from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton, QMessageBox
)
from bbdd.db_config import conectar_db
from core import productos  # Suponiendo que moviste esa clase allí


class AltaProductoDialog(QDialog):
    def __init__(self, sesion: dict):
        super().__init__()
        self.sesion = sesion
        self.setWindowTitle("➕ Alta de nuevo producto")
        self.setMinimumSize(400, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Nombre del producto:"))
        self.campo_nombre = QLineEdit()
        layout.addWidget(self.campo_nombre)

        layout.addWidget(QLabel("Stock inicial:"))
        self.campo_stock = QSpinBox()
        self.campo_stock.setRange(0, 100000)
        self.campo_stock.setValue(0)
        layout.addWidget(self.campo_stock)

        self.btn_guardar = QPushButton("Crear producto")
        self.btn_guardar.clicked.connect(self.crear_producto)
        layout.addWidget(self.btn_guardar)

        self.setLayout(layout)

    def crear_producto(self):
        nombre = self.campo_nombre.text().strip()
        stock = self.campo_stock.value()

        if not nombre:
            QMessageBox.warning(self, "Faltan datos", "Debés ingresar un nombre para el producto.")
            return

        if stock <= 0:
            QMessageBox.warning(self, "Stock inválido", "El stock inicial debe ser mayor a cero.")
            return
    
        try:
            conn = conectar_db()
            cur = conn.cursor()

            generador = productos.GeneradorEAN13(cur)
            codigo = generador.generar_codigo_unico()

            cur.execute("""
                INSERT INTO productos (nombre, stock, codigo_barra)
                VALUES (%s, %s, %s)
            """, (nombre, stock, codigo))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Éxito", f"✅ Producto creado con código:\n{codigo}")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el producto.\n{e}")
