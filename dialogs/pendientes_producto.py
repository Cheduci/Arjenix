from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
)
from core.productos import *
from dialogs.aprobar_producto import AprobarProductoDialog

class PendientesDeAprobacion(QDialog):
    def __init__(self, sesion: dict, config_sistema: dict):
        super().__init__()
        self.sesion = sesion
        self.config_sistema = config_sistema
        self.setWindowTitle("🟡 Productos pendientes de aprobación")
        self.setMinimumSize(720, 440)
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
        self.filtro.setPlaceholderText("Nombre del producto")
        self.filtro.textChanged.connect(self.aplicar_filtro)
        buscador.addWidget(self.filtro)
        layout.addLayout(buscador)

        # 📋 Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Código", "Stock", "Fecha"])
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.cellDoubleClicked.connect(self.aprobar_producto)
        self.tabla.itemSelectionChanged.connect(self.actualizar_boton_aprobar)
        layout.addWidget(self.tabla)

        # ✅ Botón aprobar seleccionado
        self.btn_aprobar = QPushButton("✅ Aprobar seleccionado")
        self.btn_aprobar.clicked.connect(self.aprobar_seleccionado)
        self.btn_aprobar.setEnabled(False)
        layout.addWidget(self.btn_aprobar)

        # 🧩 Botón cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)

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
        texto = texto.lower()
        filtrados = [
            p for p in self.todos
            if texto in p["nombre"].lower() or texto in p["codigo_barra"]
        ]
        self.mostrar_productos(filtrados)

    def aprobar_producto(self, fila, _col):
        codigo = self.tabla.item(fila, 1).text()
        dialogo = AprobarProductoDialog(self.sesion, self.config_sistema, codigo)
        if dialogo.exec():
            self.cargar_productos()
    
    def aprobar_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            QMessageBox.information(self, "Sin selección", "Seleccioná un producto para aprobar.")
            return

        self.aprobar_producto(fila, 0)
    
    def actualizar_boton_aprobar(self):
        tiene_seleccion = self.tabla.currentRow() != -1
        self.btn_aprobar.setEnabled(tiene_seleccion)
