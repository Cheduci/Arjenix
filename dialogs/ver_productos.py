from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QPushButton, QHBoxLayout, QLabel, QLineEdit
)
from PySide6.QtGui import QColor
from core import productos as pd
from dialogs.ficha_producto import FichaProductoDialog

class VerProductosDialog(QDialog):
    def __init__(self, sesion: dict, config_sistema: dict):
        super().__init__()
        self.sesion = sesion
        self.config_sistema = config_sistema
        self.setWindowTitle("📋 Todos los productos")
        self.setMinimumSize(720, 500)
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 🔍 Buscador
        buscador = QHBoxLayout()
        buscador.addWidget(QLabel("Filtrar:"))
        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText("Nombre del producto")
        self.filtro.textChanged.connect(self.aplicar_filtro)
        buscador.addWidget(self.filtro)
        layout.addLayout(buscador)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Código", "Categoría", "Stock", "Precio"])
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.cellDoubleClicked.connect(self.abrir_ficha_producto)
        self.tabla.itemSelectionChanged.connect(self.actualizar_boton_ver)
        layout.addWidget(self.tabla)

        self.btn_ver_detalle = QPushButton("🧾 Ver detalle del producto")
        self.btn_ver_detalle.setEnabled(False)
        self.btn_ver_detalle.clicked.connect(self.abrir_producto_seleccionado)
        layout.addWidget(self.btn_ver_detalle)
        self.setLayout(layout)

    def cargar_datos(self, productos=None):
        if productos is None:
            self.todos_los_productos = pd.buscar_productos()
            productos = self.todos_los_productos
        self.productos = productos
        self.tabla.setRowCount(len(productos))
        for i, p in enumerate(self.productos):
            nombre_item = QTableWidgetItem(p["nombre"])
            codigo_item = QTableWidgetItem(p["codigo_barra"])
            categoria_item = QTableWidgetItem(p["categoria"])
            stock_item = QTableWidgetItem(str(p["stock_actual"]))
            precio_str = f"${(p['precio_venta'] or 0):.2f}"
            precio_item = QTableWidgetItem(precio_str)

            # 🎨 Si el producto no está activo, pintamos en gris
            if p["estado"] != "activo":
                for item in [nombre_item, codigo_item, categoria_item, stock_item, precio_item]:
                    item.setForeground(QColor("gray"))

            self.tabla.setItem(i, 0, nombre_item)
            self.tabla.setItem(i, 1, codigo_item)
            self.tabla.setItem(i, 2, categoria_item)
            self.tabla.setItem(i, 3, stock_item)
            self.tabla.setItem(i, 4, precio_item)


    def abrir_ficha_producto(self, fila, _col):
        codigo = self.tabla.item(fila, 1).text()
        dialogo = FichaProductoDialog(self.sesion, self.config_sistema, codigo)
        dialogo.producto_actualizado.connect(self.cargar_datos)
        dialogo.exec()
        
    def actualizar_boton_ver(self):
        tiene_seleccion = self.tabla.currentRow() != -1
        self.btn_ver_detalle.setEnabled(tiene_seleccion)

    def abrir_producto_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            return
        self.abrir_ficha_producto(fila, 0)
    
    def aplicar_filtro(self, texto: str):
        texto = texto.lower()
        filtrados = [
            p for p in self.todos_los_productos
            if texto in p["nombre"].lower()
            or texto in p["categoria"].lower()
            or texto in str(p["codigo_barra"] or "").lower()
        ]
        self.cargar_datos(filtrados)