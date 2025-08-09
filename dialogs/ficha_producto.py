from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
    QMessageBox, QSpinBox, QDoubleSpinBox, QInputDialog, QGroupBox, QFileDialog
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, Signal
from core import productos
from modulos import camara
from helpers.dialogos import obtener_codigo
from typing import Literal
from helpers.exportar import exportar_codigo_pdf

class FichaProductoDialog(QDialog):
    producto_actualizado = Signal()

    def __init__(self, sesion: dict, config_sistema: dict, codigo: str):
        super().__init__()
        self.sesion = sesion
        self.config_sistema = config_sistema
        self.codigo = codigo
        self.setWindowTitle(f"📄 Ficha del producto — {codigo}")
        self.setMinimumSize(600, 400)
        self.mensaje_mostrado = False
        self.setup_ui()
        self.cargar_datos()
        self.codigo_confirmado = None

    def setup_ui(self):
        # Layout principal: horizontal (izquierda contenido, derecha acciones)
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # 🧱 Panel izquierdo (información del producto)
        left_panel = QVBoxLayout()
    
        # 🖼️ Imagen
        self.imagen = QLabel()
        self.imagen.setAlignment(Qt.AlignCenter)
        left_panel.addWidget(self.imagen)

        # Información general
        info_group = QGroupBox("📦 Información del producto")
        info_layout = QVBoxLayout()
        self.nombre = QLabel()
        font = self.nombre.font()
        font.setPointSize(14)
        font.setBold(True)
        self.nombre.setFont(font)
        self.nombre.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.nombre)
        self.codigo_label = QLabel()
        info_layout.addWidget(self.codigo_label)
        self.descripcion = QTextEdit()
        self.descripcion.setReadOnly(True)
        self.descripcion.setPlaceholderText("Sin descripción disponible")
        info_layout.addWidget(self.descripcion)
        info_group.setLayout(info_layout)
        left_panel.addWidget(info_group)

        # 📊 Grupo: Stock
        stock_group = QGroupBox("📈 Inventario")
        stock_layout = QVBoxLayout()

        # 🔢 Campo stock actual
        fila_stock = QHBoxLayout()
        fila_stock.addWidget(QLabel("Stock actual:"))
        self.campo_stock = QSpinBox()
        self.campo_stock.setRange(0, 100000)
        self.campo_stock.setEnabled(False)
        fila_stock.addWidget(self.campo_stock)
        stock_layout.addLayout(fila_stock)

        # 🔢 Campo stock mínimo
        fila_minimo = QHBoxLayout()
        self.label_stock_minimo = QLabel("Stock mínimo:")
        fila_minimo.addWidget(self.label_stock_minimo)
        self.campo_stock_minimo = QSpinBox()
        self.campo_stock_minimo.setRange(0, 100000)
        self.campo_stock_minimo.setEnabled(False)
        fila_minimo.addWidget(self.campo_stock_minimo)
        stock_layout.addLayout(fila_minimo)

        stock_group.setLayout(stock_layout)
        left_panel.addWidget(stock_group)

        # 💰 Grupo: Precios
        precios_group = QGroupBox("💰 Precios")
        precio_layout = QHBoxLayout()
        self.precio_compra = QDoubleSpinBox()
        self.precio_compra.setPrefix("$")
        self.precio_compra.setMaximum(999999)
        self.precio_compra.setDecimals(2)
        self.precio_compra.setEnabled(False)
        self.precio_compra.setToolTip("Precio de compra del proveedor")
        self.precio_venta = QDoubleSpinBox()
        self.precio_venta.setPrefix("$")
        self.precio_venta.setMaximum(999999)
        self.precio_venta.setDecimals(2)
        self.precio_venta.setEnabled(False)
        self.precio_venta.setToolTip("Precio de venta al cliente")
        precio_layout.addWidget(QLabel("Compra:"))
        precio_layout.addWidget(self.precio_compra)
        precio_layout.addSpacing(30)
        precio_layout.addWidget(QLabel("Venta:"))
        precio_layout.addWidget(self.precio_venta)
        precios_group.setLayout(precio_layout)
        left_panel.addWidget(precios_group)

        left_panel.addStretch()
        main_layout.addLayout(left_panel)

        # 🧱 Panel derecho (botones de acciones)
        right_panel = QVBoxLayout()

        # 🛠️ Grupo: Acciones disponibles
        acciones_group = QGroupBox("⚙️ Acciones")
        self.acciones_layout = QVBoxLayout()

        # Grupo: Códigos de barras
        self.codigo_barra_group = QGroupBox("📑 Código de barras")

        self.label_codigo_confirmado = QLabel(f"🆔 Código actual: {self.codigo}")
        self.label_codigo_confirmado.setStyleSheet("font-weight: bold; color: #333; padding: 4px;")
        
        self.botones_codigos = QHBoxLayout()
        self.btn_escanear = QPushButton("📷 Escanear")
        self.btn_manual = QPushButton("✍️ Ingresar")
        self.btn_manual.clicked.connect(lambda: self._manejar_codigo("manual"))
        self.btn_escanear.clicked.connect(lambda: self._manejar_codigo("escanear"))
        self.botones_codigos.addWidget(self.btn_escanear)
        self.botones_codigos.addWidget(self.btn_manual)
        
        self.btn_guardar_codigo = QPushButton("💾 Guardar código")
        self.btn_guardar_codigo.clicked.connect(self.guardar_codigo)
        layout_codigo = QVBoxLayout()
        layout_codigo.addWidget(self.label_codigo_confirmado)
        layout_codigo.addLayout(self.botones_codigos)
        layout_codigo.addWidget(self.btn_guardar_codigo)

        self.codigo_barra_group.setLayout(layout_codigo)

        # 
        self.btn_guardar_stock = QPushButton("💾 Actualizar stock")
        self.btn_guardar_precios = QPushButton("💾 Actualizar precios")
        self.btn_estado = QPushButton()
        self.btn_eliminar = QPushButton("🗑️ Eliminar permanentemente")
        self.btn_exportar = QPushButton("📤 Exportar etiqueta PDF")

        self.btn_guardar_stock.clicked.connect(self.actualizar_stock)
        self.btn_guardar_precios.clicked.connect(self.actualizar_precios)
        self.btn_estado.clicked.connect(self.toggle_estado_producto)
        self.btn_eliminar.clicked.connect(self.eliminar_producto)
        self.btn_exportar.clicked.connect(self.exportar_etiqueta_pdf)

        # self.acciones_layout.addWidget(self.btn_guardar_stock)
        # self.acciones_layout.addWidget(self.btn_guardar_precios)
        # self.acciones_layout.addWidget(self.btn_estado)
        self.acciones_layout.addWidget(self.btn_exportar)
        self.acciones_layout.addStretch()

        # 📸 Grupo: Actualizar foto
        self.foto_group = QGroupBox("Actualizar foto")
        self.foto_layout = QHBoxLayout()

        btn_examinar = QPushButton("Examinar...")
        btn_examinar.clicked.connect(self.examinar_foto)
        self.foto_layout.addWidget(btn_examinar)

        btn_sacar = QPushButton("Sacar foto")
        btn_sacar.clicked.connect(self.sacar_foto)
        self.foto_layout.addWidget(btn_sacar)

        self.foto_group.setLayout(self.foto_layout)

        acciones_group.setLayout(self.acciones_layout)
        right_panel.addWidget(acciones_group)
        main_layout.addLayout(right_panel)


    def cargar_datos(self):
        self.producto = productos.obtener_producto_por_codigo(self.codigo)
        if not self.producto:
            QMessageBox.critical(self, "Error", "No se pudo cargar el producto.")
            self.reject()
            return

        estado = self.producto["estado"]
        nombre = self.producto["nombre"]
        estado_tag = f"<h2>{nombre}</h2>"

        if estado == "activo":
            self.nombre.setText(estado_tag)
            self.btn_estado.setText("⛔ Inactivar producto")
            self.btn_estado.setEnabled(True)

        elif estado == "inactivo":
            self.nombre.setText(f"<h2 style='color:gray'>{nombre} (INACTIVO)</h2>")
            self.btn_estado.setText("✅ Activar producto")
            self.btn_estado.setEnabled(True)

            if not self.mensaje_mostrado:
                QMessageBox.information(
                    self,
                    "Producto inactivo",
                    "⚠️ Este producto está actualmente inactivo.\nNo puede ser vendido ni utilizado en operaciones.",
                    QMessageBox.Ok
                )
                self.mensaje_mostrado = True

        elif estado == "pendiente":
            self.nombre.setText(f"<h2 style='color:orange'>{nombre} (PENDIENTE)</h2>")
            self.btn_estado.setText("⏳ Estado pendiente")
            self.btn_estado.setEnabled(False)

            if not self.mensaje_mostrado:
                QMessageBox.information(
                    self,
                    "Producto pendiente",
                    "ℹ️ Este producto está en estado pendiente.\nRevisá sus datos antes de usarlo.",
                    QMessageBox.Ok
                )
                self.mensaje_mostrado = True
            
        # 📄 Info básica
        
        self.codigo_label.setText(f"Código: {self.producto['codigo_barra']} — Categoría: {self.producto['categoria']}")
        self.descripcion.setText(self.producto["descripcion"])

        self.campo_stock.setValue(self.producto["stock_actual"])
        self.campo_stock_minimo.setValue(self.producto.get("stock_minimo", 0))

        if self.producto["stock_actual"] < self.producto.get("stock_minimo", 0):
            self.campo_stock.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.campo_stock.setStyleSheet("")

        self.precio_compra.setValue(self.producto["precio_compra"])
        self.precio_venta.setValue(self.producto["precio_venta"])
        

        # 🖼️ Imagen si existe
        foto_bytes = self.producto.get("foto")
        if foto_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(foto_bytes)
            self.imagen.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.imagen.setText("📷 Sin imagen")


        # 🔒 Permisos según rol
        rol = self.sesion["rol"]

        if rol in ["dueño", "gerente"]:
            self.precio_compra.setEnabled(True)
            self.precio_venta.setEnabled(True)
            self.campo_stock_minimo.setVisible(True)
            self.acciones_layout.addWidget(self.btn_guardar_precios)
            self.acciones_layout.addWidget(self.foto_group)
            self.acciones_layout.addWidget(self.btn_estado)
            self.label_stock_minimo.show()
            self.campo_stock_minimo.show()
            if self.config_sistema.get("modo_codigo_barra") != "auto":
                self.acciones_layout.addWidget(self.codigo_barra_group)
            # self.codigo_barra_group.setVisible(True)
        else:
            self.label_stock_minimo.hide()
            self.campo_stock_minimo.hide()
            # self.codigo_barra_group.setVisible(False)

        if rol == "dueño":
            self.campo_stock.setEnabled(True)
            self.campo_stock_minimo.setEnabled(True)
            self.acciones_layout.addWidget(self.btn_guardar_stock)
            self.acciones_layout.addWidget(self.btn_eliminar)

    # Métodos a definir para acciones:
    def actualizar_stock(self): 
        nuevo_stock = self.campo_stock.value()
        stock_minimo = self.campo_stock_minimo.value()

        confirm = QMessageBox.question(
            self, "Confirmar",
            f"¿Actualizar el stock a {nuevo_stock} unidades?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if productos.modificar_stock(self.codigo, nuevo_stock, stock_minimo):
                QMessageBox.information(self, "Éxito", "✅ Stock actualizado correctamente.")
                self.producto_actualizado.emit()  # <--- EMITIR AQUÍ
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar el stock.")

    def actualizar_precios(self): 
        compra = self.precio_compra.value()
        venta = self.precio_venta.value()

        if compra > venta:
            QMessageBox.warning(self, "Precios inconsistentes", "El precio de venta no puede ser menor que el de compra.")
            return

        confirm = QMessageBox.question(
            self, "Confirmar",
            f"¿Actualizar los precios?\nCompra: ${compra:.2f}\nVenta: ${venta:.2f}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            if productos.actualizar_precios(self.codigo, compra, venta):
                QMessageBox.information(self, "Éxito", "✅ Precios actualizados.")
                self.producto_actualizado.emit()  # <--- EMITIR AQUÍ
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "No se pudieron actualizar los precios.")
        
    def toggle_estado_producto(self):
        estado = self.producto["estado"]

        if estado == "activo":
            confirmado = QMessageBox.question(
                self, "Inactivar", "¿Querés inactivar este producto?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirmado == QMessageBox.Yes:
                productos.inactivar_producto(self.codigo)
                self.producto_actualizado.emit()  # <--- EMITIR AQUÍ
        elif estado == "inactivo":
            confirmado = QMessageBox.question(
                self, "Reactivar", "¿Querés reactivar este producto?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirmado == QMessageBox.Yes:
                productos.reactivar_producto(self.codigo)
                self.producto_actualizado.emit()  # <--- EMITIR AQUÍ
        self.cargar_datos()

    
    def eliminar_producto(self): 
        confirm = QMessageBox.critical(self, "Eliminar permanentemente",
            "⚠️ Esta acción es irreversible.\n¿Deseás continuar?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if productos.eliminar_producto(self.codigo):
                QMessageBox.information(self, "Eliminado", "🗑️ Producto eliminado del sistema.")
                self.producto_actualizado.emit()  # <--- EMITIR AQUÍ
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el producto.")
    
    def exportar_etiqueta_pdf(self):
        cantidad, ok = QInputDialog.getInt(self, "Cantidad de etiquetas", "¿Cuántas etiquetas querés imprimir?", 1, 1, 999)
        if not ok:
            return

        nombre = self.producto["nombre"]
        codigo = self.producto["codigo_barra"]
        precio = self.producto["precio_venta"]

        ruta, error = exportar_codigo_pdf(nombre, codigo, precio, cantidad)
        if ruta:
            QMessageBox.information(self, "Etiqueta exportada", f"✅ Etiqueta guardada en:\n{ruta}")
        else:
            QMessageBox.critical(self, "Error", f"❌ No se pudo exportar la etiqueta.\nDetalles: {error}")

    def actualizar_foto(self, foto_bytes):
        """Actualiza la imagen en la interfaz y la base de datos."""
        if not foto_bytes:
            QMessageBox.warning(self, "Sin imagen", "No se recibió ninguna imagen.")
            return

        # Actualizar QLabel
        pixmap = QPixmap()
        pixmap.loadFromData(foto_bytes)
        self.imagen.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        # Guardar en base de datos
        exito = productos.actualizar_foto(self.codigo, foto_bytes)
        if exito:
            QMessageBox.information(self, "Foto actualizada", "✅ La foto del producto fue actualizada.")
            self.producto_actualizado.emit()  # <--- EMITIR AQUÍ
        else:
            QMessageBox.critical(self, "Error", "No se pudo actualizar la foto en la base de datos.")

    def examinar_foto(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if ruta:
            with open(ruta, "rb") as f:
                self.foto_bytes = f.read()
            self.actualizar_foto(self.foto_bytes)

    def sacar_foto(self):
        foto = camara.capturar_foto()
        if foto:
            self.foto_bytes = foto
            self.actualizar_foto(self.foto_bytes)

    def _manejar_codigo(self, modo: Literal["manual", "escanear"]):
        codigo = obtener_codigo(self, modo, self.codigo_confirmado)
        if codigo:
            self.codigo_confirmado = codigo
            self.label_codigo_confirmado.setText(f"🆔 Código: {codigo}")

    def guardar_codigo(self):
        if self.codigo_confirmado:
            ok,error = productos.guardar_codigo(self.codigo_confirmado, id_producto=self.producto["id"])
            if ok:
                self.codigo = self.codigo_confirmado
                self.cargar_datos()  # Recargar datos para mostrar el nuevo código
                self.producto_actualizado.emit()
                QMessageBox.information(self, "Código guardado", "✅ El código fue guardado exitosamente.")
            else:
                QMessageBox.warning(self, "Error", f"⚠️ No se pudo guardar el código.\nDetalles: {error}")
        else:
            QMessageBox.warning(self, "Sin código", "⚠️ No hay ningún código para guardar.")