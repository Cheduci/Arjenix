from PySide6.QtWidgets import (QDialog, QHBoxLayout, QTableWidget, QAbstractItemView, QVBoxLayout, 
        QPushButton, QMessageBox, QInputDialog)
from core.productos import registrar_reposicion
from dialogs.buscar_producto import BuscarProductoDialog
from helpers.dialogos import pedir_codigo_barras, solicitar_cantidad
from core.productos import obtener_producto_por_codigo
from modulos.camara import escanear_codigo_opencv

class RegistrarReposicionDialog(QDialog):
    def __init__(self, sesion, codigo_barra, nombre, stock_actual, parent=None):
        super().__init__(parent)
        self.sesion = sesion
        self.codigo_barra = codigo_barra
        self.nombre_producto = nombre
        self.stock_actual = stock_actual
        self.setWindowTitle("📦 Registrar reposición")
        self.setFixedSize(400, 280)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)

        # 🧱 Panel izquierdo: tabla principal
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Código de barra", "Cantidad"])
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.tabla, stretch=3)

        # 🧱 Panel derecho: acciones
        panel_derecho = QVBoxLayout()

        # 🔼 Botones superiores
        btn_escanear = QPushButton("📷 Escanear código")
        btn_escanear.clicked.connect(self.abrir_escanear_codigo)  # ya implementado

        btn_manual = QPushButton("⌨️ Ingreso manual")
        btn_manual.clicked.connect(self.abrir_ingreso_manual)  # ya implementado

        btn_buscar = QPushButton("🔍 Buscar producto")
        btn_buscar.clicked.connect(self.abrir_buscar_producto)  # ya implementado

        panel_derecho.addWidget(btn_buscar)
        panel_derecho.addWidget(btn_escanear)
        panel_derecho.addWidget(btn_manual)
        panel_derecho.addSpacing(30)

        # 🔽 Botones inferiores
        btn_modificar = QPushButton("✏️ Modificar cantidad")
        btn_modificar.clicked.connect(self.modificar_seleccionado)

        btn_confirmar = QPushButton("✅ Confirmar reposiciones")
        btn_confirmar.clicked.connect(self.confirmar_todas)

        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        panel_derecho.addStretch()
        panel_derecho.addWidget(btn_modificar)
        panel_derecho.addWidget(btn_confirmar)
        panel_derecho.addWidget(btn_cancelar)

        layout.addLayout(panel_derecho, stretch=1)

    def abrir_escanear_codigo(self):
        codigo = escanear_codigo_opencv()

        try:
            producto = obtener_producto_por_codigo(codigo)
        except RuntimeError as err:
            QMessageBox.warning(self, "Error de escaneo", str(err))
            return

        if producto:
            self.agregar_a_reposiciones(producto)

    def abrir_buscar_producto(self):
        dlg = BuscarProductoDialog(self.sesion, modo="seleccionar",parent=self)
        dlg.exec()

    def abrir_ingreso_manual(self):
        try:
            codigo = pedir_codigo_barras(self)
            producto = obtener_producto_por_codigo(codigo)
        except RuntimeError as err:
            QMessageBox.warning(self, "Error de consulta", str(err))
            return

        if not producto:
            QMessageBox.warning(self, "Producto no encontrado", f"No se encontró el código: {codigo}")
            return

        self.agregar_a_reposiciones(producto)

    def modificar_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Sin selección", "Seleccioná un producto para modificar.")
            return

        actual = self.reposiciones_en_curso[fila]
        nueva_cantidad, ok = QInputDialog.getInt(self, "Modificar cantidad", f"{actual['nombre']}", actual['cantidad'], 1, 9999)
        if ok:
            actual["cantidad"] = nueva_cantidad
            self.refrescar_tabla()

    def confirmar_todas(self):
        errores = []
        for item in self.reposiciones_en_curso:
            exito = registrar_reposicion(
                self.sesion,
                codigo_barra=item["codigo_barra"],
                cantidad=item["cantidad"],
                usuario=self.usuario_actual  # o capturado en el diálogo
            )
            if not exito:
                errores.append(item["codigo_barra"])
        
        if errores:
            QMessageBox.warning(self, "Error parcial", f"Algunos productos no se pudieron registrar:\n" + "\n".join(errores))
        else:
            QMessageBox.information(self, "Reposiciones registradas", "Todas las reposiciones fueron exitosamente registradas.")
            self.accept()
