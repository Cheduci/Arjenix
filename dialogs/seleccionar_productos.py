from PySide6.QtWidgets import (QDialog, QHBoxLayout, QListWidget,QVBoxLayout,QPushButton,)
from dialogs.buscar_producto import BuscarProductoDialog
from core import productos

class SeleccionarProductosDialog(QDialog):
    def __init__(self, sesion, modo="seleccionar", parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Seleccionar productos")
        self.setMinimumSize(700, 480)
        self.sesion = sesion
        self.modo = modo
        self.productos_seleccionados = []  # lista de tuplas (codigo, nombre)

        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()

        # Lista principal
        self.lista = QListWidget()
        layout.addWidget(self.lista, 3)  # Más espacio

        # Panel lateral
        panel = QVBoxLayout()

        self.btn_agregar = QPushButton("Agregar")
        self.btn_agregar.clicked.connect(self.agregar_producto)
        panel.addWidget(self.btn_agregar)

        self.btn_borrar = QPushButton("Borrar")
        self.btn_borrar.clicked.connect(self.borrar_producto)
        panel.addWidget(self.btn_borrar)

        panel.addStretch()

        self.btn_aceptar = QPushButton("Aceptar")
        self.btn_aceptar.clicked.connect(self.aceptar)
        panel.addWidget(self.btn_aceptar)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        panel.addWidget(self.btn_cancelar)

        layout.addLayout(panel, 1)

        self.setLayout(layout)

    def agregar_producto(self):
        dlg = BuscarProductoDialog(self.sesion, modo=self.modo, parent=self)
        if dlg.exec() == QDialog.Accepted:
            codigo, _ = dlg.obtener_codigo_seleccionado()
            # Podés usar productos.obtener_por_codigo() para traer el nombre
            info = productos.obtener_producto_por_codigo(codigo)
            nombre = info.get("nombre", "Sin nombre") if info else "Sin nombre"
            self.productos_seleccionados.append((codigo, nombre))
            self.lista.addItem(f"{nombre} ({codigo})")

    def borrar_producto(self):
        fila = self.lista.currentRow()
        if fila != -1:
            self.lista.takeItem(fila)
            del self.productos_seleccionados[fila]

    def obtener_codigos_seleccionados(self):
        return [p[0] for p in self.productos_seleccionados]
    
    def obtener_nombres_seleccionados(self) -> list[str]:
        return [c[1] for c in self.productos_seleccionados]
    
    def aceptar(self):
        self.codigos_seleccionados = self.obtener_codigos_seleccionados()
        self.accept()
