from PySide6.QtWidgets import (QDialog, QHBoxLayout, QTableWidget, QAbstractItemView, QVBoxLayout, 
        QPushButton, QMessageBox, QInputDialog, QTableWidgetItem)
from dialogs.buscar_producto import BuscarProductoDialog
from helpers.dialogos import pedir_codigo_barras, solicitar_cantidad
from core.productos import obtener_producto_por_codigo, modificar_stock, obtener_stock_actual
from core.reposiciones import registrar_reposicion
from modulos.camara import escanear_codigo_opencv
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl

class RegistrarReposicionDialog(QDialog):
    def __init__(self, sesion, parent=None):
        super().__init__(parent)
        self.sesion = sesion
        self.setWindowTitle("📦 Registrar reposición")
        self.setFixedSize(500, 380)

        self.reposiciones_en_curso = []
        self.beep = QSoundEffect()
        self.beep.setSource(QUrl.fromLocalFile("sonidos/beep.wav"))
        self.beep.setVolume(0.5)
        
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
        if not codigo:
            return

        producto = None
        try:
            producto = obtener_producto_por_codigo(codigo)
        except RuntimeError as err:
            QMessageBox.warning(self, "Error de escaneo", str(err))
            return

        if producto:
            self.manejar_producto_identificado(producto)

    def abrir_buscar_producto(self):
        dlg = BuscarProductoDialog(self.sesion, modo="estadistica",parent=self)
        if dlg.exec() == QDialog.Accepted:
            codigo, nombre = dlg.obtener_codigo_seleccionado()
            producto = obtener_producto_por_codigo(codigo)
            if producto:
                self.manejar_producto_identificado(producto)


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

        self.manejar_producto_identificado(producto)

    def modificar_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Sin selección", "Seleccioná un producto para modificar.")
            return

        actual = self.reposiciones_en_curso[fila]
        nombre = actual["producto"]["nombre"]
        cantidad_actual = actual["cantidad"]

        nueva_cantidad, ok = QInputDialog.getInt(self, "Modificar cantidad", f"{nombre}", cantidad_actual, 1, 9999)
        
        if ok:
            actual["cantidad"] = nueva_cantidad
            self.refrescar_tabla()

    def confirmar_todas(self):
        if not self.reposiciones_en_curso:
            QMessageBox.information(self, "Sin reposiciones", "No hay productos en la lista para confirmar.")
            return

        respuesta = QMessageBox.question(
            self,
            "Confirmar reposiciones",
            f"¿Deseás registrar las {len(self.reposiciones_en_curso)} reposiciones?",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta != QMessageBox.Yes:
            return

        errores = []

        for item in self.reposiciones_en_curso:
            producto = item["producto"]
            cantidad_reponer = item["cantidad"]
            codigo = producto["codigo_barra"]
            motivo = item.get("motivo", "Reposición manual desde panel")  # si lo tenés
            usuario_id = self.sesion.get("id")

            try:
                stock_actual = obtener_stock_actual(codigo)
                nuevo_stock = stock_actual + cantidad_reponer
                exito_stock = modificar_stock(codigo, nuevo_stock)
                exito_repo = registrar_reposicion(codigo, cantidad_reponer, usuario_id, motivo)

                if not (exito_stock and exito_repo):
                    errores.append(f"{producto['nombre']}: error al actualizar el stock.")
            except Exception as e:
                errores.append(f"{producto['nombre']}: {str(e)}")

        if errores:
            QMessageBox.warning(
                self,
                "Errores durante la confirmación",
                "Ocurrieron problemas al registrar algunas reposiciones:\n\n" + "\n".join(errores)
            )
        else:
            QMessageBox.information(
                self,
                "Reposiciones confirmadas",
                f"Todas las reposiciones fueron registradas exitosamente."
            )
            self.accept()  # Cierra el diálogo con éxito


    def manejar_producto_identificado(self, producto):
        if any(p["producto"]["codigo"] == producto["codigo"] for p in self.reposiciones_en_curso):
            QMessageBox.information(self, "Ya agregado", f"El producto '{producto['nombre']}' ya está en la lista.")
            return
        
        cantidad = solicitar_cantidad(self, descripcion=producto["nombre"], stock=producto.get("stock", 99))
        if cantidad is None:
            return

        self.beep.play()

        fila = self.tabla.rowCount()
        self.tabla.insertRow(fila)
        self.tabla.setItem(fila, 0, QTableWidgetItem(producto["nombre"]))
        self.tabla.setItem(fila, 1, QTableWidgetItem(producto["codigo_barra"]))
        self.tabla.setItem(fila, 2, QTableWidgetItem(str(cantidad)))

        self.reposiciones_en_curso.append({
            "producto": producto,
            "cantidad": cantidad
        })

        self.refrescar_tabla()

    def refrescar_tabla(self):
        self.tabla.setRowCount(len(self.reposiciones_en_curso))
        for fila, item in enumerate(self.reposiciones_en_curso):
            producto = item["producto"]
            cantidad = item["cantidad"]

            self.tabla.setItem(fila, 0, QTableWidgetItem(producto["nombre"]))
            self.tabla.setItem(fila, 1, QTableWidgetItem(producto["codigo_barra"]))
            self.tabla.setItem(fila, 2, QTableWidgetItem(str(cantidad)))
