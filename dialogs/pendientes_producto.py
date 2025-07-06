from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt
from core.productos import *
from dialogs.aprobar_producto import AprobarProductoDialog

class PendientesDeAprobacion(QWidget):
    def __init__(self, sesion: dict):
        super().__init__()
        self.sesion = sesion
        self.setWindowTitle("🟡 Productos pendientes de aprobación")
        self.setMinimumSize(700, 400)
        self.setup_ui()
        self.cargar_productos()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 🧮 Contador de pendientes
        self.label_total = QLabel("🟡 Productos pendientes: 0")
        font = self.label_total.font()
        font.setPointSize(10)
        font.setBold(True)
        self.label_total.setFont(font)
        layout.addWidget(self.label_total)

        # 🔍 Buscador
        buscador = QHBoxLayout()
        buscador.addWidget(QLabel("Buscar:"))
        self.filtro = QLineEdit()
        self.filtro.textChanged.connect(self.aplicar_filtro)
        buscador.addWidget(self.filtro)
        layout.addLayout(buscador)

        # 📋 Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Código", "Stock", "Fecha"])
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.cellDoubleClicked.connect(self.aprobar_producto)
        layout.addWidget(self.tabla)

        self.setLayout(layout)

    def cargar_productos(self):
        self.todos = obtener_pendientes_de_aprobacion()
        self.label_total.setText(f"🟡 Productos pendientes: {len(self.todos)}")
        self.mostrar_productos(self.todos)

    def mostrar_productos(self, productos: list):
        self.tabla.setRowCount(len(productos))
        for i, p in enumerate(productos):
            self.tabla.setItem(i, 0, QTableWidgetItem(p["nombre"]))
            self.tabla.setItem(i, 1, QTableWidgetItem(p["codigo_barra"]))
            self.tabla.setItem(i, 2, QTableWidgetItem(str(p["stock_actual"])))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(p["fecha_creacion"])))
        self.tabla.resizeColumnsToContents()

    def aplicar_filtro(self, texto: str):
        filtrados = [p for p in self.todos if texto.lower() in p["nombre"].lower()]
        self.mostrar_productos(filtrados)

    def aprobar_producto(self, fila, _col):
        codigo = self.tabla.item(fila, 1).text()
        dialogo = AprobarProductoDialog(self.sesion, codigo)
        if dialogo.exec():
            self.cargar_productos()
