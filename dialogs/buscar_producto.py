from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QSpinBox, QTableWidget, QTableWidgetItem
)
from core import productos  # Debe exponer una función para búsqueda filtrada
from dialogs.ficha_producto import FichaProductoDialog
from helpers.dialogos import solicitar_cantidad

class BuscarProductoDialog(QDialog):
    def __init__(self, sesion:dict, modo="ver", parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 Buscar producto")
        self.setMinimumSize(720, 500)
        self.sesion = sesion
        self.modo = modo # "ver" o "seleccionar"
        self.codigo_seleccionado = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 🔍 Filtros de búsqueda
        filtro_layout = QHBoxLayout()

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre o descripción...")
        filtro_layout.addWidget(self.input_nombre)

        self.input_codigo = QLineEdit()
        self.input_codigo.setPlaceholderText("Código de barras")
        filtro_layout.addWidget(self.input_codigo)

        self.combo_categoria = QComboBox()
        self.combo_categoria.addItem("Todas las categorías")
        self.combo_categoria.addItems(productos.listar_categorias())
        filtro_layout.addWidget(self.combo_categoria)

        self.btn_buscar = QPushButton("Buscar")
        self.btn_buscar.clicked.connect(self.buscar)
        filtro_layout.addWidget(self.btn_buscar)

        self.btn_aceptar = QPushButton("Aceptar")
        self.btn_aceptar.setEnabled(False)
        self.btn_aceptar.clicked.connect(self.seleccionar_producto)
        layout.addWidget(self.btn_aceptar)
        

        layout.addLayout(filtro_layout)

        # 📋 Tabla de resultados
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Código", "Categoría", "Stock", "Precio"])
        self.tabla.cellDoubleClicked.connect(self.aceptar_producto)
        self.tabla.itemSelectionChanged.connect(self.verificar_seleccion)

        layout.addWidget(self.tabla)

        self.setLayout(layout)

    def buscar(self):
        nombre = self.input_nombre.text().strip().lower()
        codigo = self.input_codigo.text().strip()
        categoria = self.combo_categoria.currentText()

        resultados = productos.buscar_productos(
            nombre=nombre,
            codigo=codigo,
            categoria=None if categoria == "Todas las categorías" else categoria
        )

        self.tabla.setRowCount(len(resultados))
        for i, p in enumerate(resultados):
            nombre = p.get("nombre") or "Sin nombre"
            codigo = p.get("codigo_barra") or "-"
            categoria = p.get("categoria") or "Sin categoría"
            stock = p.get("stock_actual") if p.get("stock_actual") is not None else 0
            precio = p.get("precio_venta")
            precio_str = f"${precio:.2f}" if precio is not None else "—"

            self.tabla.setItem(i, 0, QTableWidgetItem(nombre))
            self.tabla.setItem(i, 1, QTableWidgetItem(codigo))
            self.tabla.setItem(i, 2, QTableWidgetItem(categoria))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(stock)))
            self.tabla.setItem(i, 4, QTableWidgetItem(precio_str))


    
    def aceptar_producto(self, fila, _col):
        codigo = self.tabla.item(fila, 1).text()  # columna con código_barra
        nombre = self.tabla.item(fila, 0).text()
        stock = int(self.tabla.item(fila, 3).text())

        cantidad = solicitar_cantidad(self, descripcion=nombre, stock=stock)
        if cantidad is None:
            return  # Usuario canceló

        if self.modo == "seleccionar":
            self.codigo_seleccionado = (codigo, cantidad)
            self.accept()
        elif self.modo == "ver":
            dlg = FichaProductoDialog(self.sesion, codigo)
            dlg.exec()

    def obtener_codigo_seleccionado(self):
        return self.codigo_seleccionado

    def seleccionar_producto(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            return
        self.codigo_seleccionado = self.tabla.item(fila, 1).text()
        self.accept()

    def verificar_seleccion(self):
        fila = self.tabla.currentRow()
        self.btn_aceptar.setEnabled(fila != -1)
