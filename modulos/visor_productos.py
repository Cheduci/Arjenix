from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from core.productos import buscar_productos  # a definir
from ficha_producto import FichaProductoDialog

class VisorProductos(QWidget):
    def __init__(self, sesion: dict):
        super().__init__()
        self.sesion = sesion
        self.setWindowTitle("📦 Productos — Arjenix")
        self.setMinimumSize(700, 500)
        self.setup_ui()
        self.cargar_productos()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 🔍 Filtro
        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Buscar:"))
        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText("Nombre o código")
        self.campo_busqueda.textChanged.connect(self.cargar_productos)
        filtro_layout.addWidget(self.campo_busqueda)
        layout.addLayout(filtro_layout)

        # 📋 Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Código", "Stock", "Precio venta", "Activo"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(self.tabla.SelectRows)
        self.tabla.setEditTriggers(self.tabla.NoEditTriggers)
        self.tabla.cellDoubleClicked.connect(self.abrir_ficha_producto)
        layout.addWidget(self.tabla)

        self.setLayout(layout)

    def cargar_productos(self):
        filtro = self.campo_busqueda.text().strip()
        productos = buscar_productos(filtro)
        self.tabla.setRowCount(len(productos))

        for fila, producto in enumerate(productos):
            self.tabla.setItem(fila, 0, QTableWidgetItem(producto["nombre"]))
            self.tabla.setItem(fila, 1, QTableWidgetItem(producto["codigo"]))
            self.tabla.setItem(fila, 2, QTableWidgetItem(str(producto["stock"])))
            self.tabla.setItem(fila, 3, QTableWidgetItem(f"${producto['precio_venta']:.2f}"))
            self.tabla.setItem(fila, 4, QTableWidgetItem("Sí" if producto["activo"] else "No"))

    def abrir_ficha_producto(self, fila, _col):
        codigo = self.tabla.item(fila, 1).text()
        dialogo = FichaProductoDialog(self.sesion, codigo)
        dialogo.exec()
        self.cargar_productos()  # refrescar después de posibles cambios
