from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QDoubleSpinBox,
    QSpinBox, QPushButton, QFileDialog, QMessageBox, QComboBox, QHBoxLayout
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from core import productos
from modulos import camara
import os

class AprobarProductoDialog(QDialog):
    def __init__(self, sesion: dict, codigo: str):
        super().__init__()
        self.sesion = sesion
        self.codigo = codigo
        self.setWindowTitle("✅ Aprobar producto")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 🔤 Nombre
        layout.addWidget(QLabel("Nombre:"))
        self.nombre = QLineEdit()
        layout.addWidget(self.nombre)

        # 📝 Descripción
        layout.addWidget(QLabel("Descripción:"))
        self.descripcion = QTextEdit()
        layout.addWidget(self.descripcion)

        # 🏷️ Categoría
        layout.addWidget(QLabel("Categoría:"))
        self.categoria = QComboBox()
        layout.addWidget(self.categoria)

        # 💰 Precio de compra
        layout.addWidget(QLabel("Precio de compra:"))
        self.precio_compra = QDoubleSpinBox()
        self.precio_compra.setPrefix("$")
        self.precio_compra.setMaximum(999999999)
        self.precio_compra.setDecimals(2)
        layout.addWidget(self.precio_compra)

        # 💸 Precio de venta
        layout.addWidget(QLabel("Precio de venta:"))
        self.precio_venta = QDoubleSpinBox()
        self.precio_venta.setPrefix("$")
        self.precio_venta.setMaximum(999999999)
        self.precio_venta.setDecimals(2)
        layout.addWidget(self.precio_venta)

        # 📦 Stock mínimo
        layout.addWidget(QLabel("Stock mínimo:"))
        self.stock_minimo = QSpinBox()
        self.stock_minimo.setRange(0, 1000000)
        layout.addWidget(self.stock_minimo)

        # 🖼️ Imagen del producto
        layout.addWidget(QLabel("Imagen del producto:"))
        self.label_imagen = QLabel("📷 Sin imagen")
        self.label_imagen.setAlignment(Qt.AlignCenter)
        self.label_imagen.setFixedHeight(200)
        layout.addWidget(self.label_imagen)

        # 🎛️ Botones: Examinar y Capturar
        hbox_foto = QHBoxLayout()
        self.btn_examinar = QPushButton("📁 Examinar")
        self.btn_capturar = QPushButton("📸 Capturar")
        self.btn_examinar.clicked.connect(self.cargar_desde_archivo)
        self.btn_capturar.clicked.connect(self.capturar_desde_camara)
        hbox_foto.addWidget(self.btn_examinar)
        hbox_foto.addWidget(self.btn_capturar)
        layout.addLayout(hbox_foto)

        # ✅ Botón aprobar
        layout.addStretch()
        self.btn_aprobar = QPushButton("✅ Aprobar producto")
        self.btn_aprobar.clicked.connect(self.aprobar_producto)
        layout.addWidget(self.btn_aprobar)

        self.setLayout(layout)

    def cargar_datos(self):
        producto = productos.obtener_producto_por_codigo(self.codigo)
        if not producto:
            QMessageBox.critical(self, "Error", "Producto no encontrado.")
            self.reject()
            return

        self.nombre.setText(producto["nombre"])
        self.descripcion.setText(producto["descripcion"] or "")
        self.precio_compra.setValue(producto.get("precio_compra", 0))
        self.precio_venta.setValue(producto.get("precio_venta", 0))
        self.stock_minimo.setValue(producto.get("stock_minimo", 0))

        # Imagen previa si hay
        foto = producto.get("foto")
        if foto and os.path.exists(foto):
            self.label_imagen.setPixmap(QPixmap(foto).scaled(200, 200, Qt.KeepAspectRatio))

    def cargar_imagen(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if ruta:
            self.imagen_seleccionada = ruta
            self.label_imagen.setPixmap(QPixmap(ruta).scaled(200, 200, Qt.KeepAspectRatio))

    def aprobar_producto(self):
        nombre = self.nombre.text().strip()
        descripcion = self.descripcion.toPlainText().strip()
        categoria = self.categoria.currentText()
        precio_venta = self.precio_venta.value()

        if not all([nombre, descripcion, categoria]) or precio_venta <= 0:
            QMessageBox.warning(self, "Faltan datos", "Completá todos los campos obligatorios.")
            return

        aprobado = productos.aprobar_producto(
            codigo=self.codigo,
            nombre=nombre,
            descripcion=descripcion,
            categoria=categoria,
            precio_venta=precio_venta,
            precio_compra=self.precio_compra.value(),
            stock_minimo=self.stock_minimo.value(),
            ruta_imagen=getattr(self, "imagen_seleccionada", None)
        )

        if aprobado:
            QMessageBox.information(self, "Listo", "🟢 Producto aprobado y activado.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo aprobar el producto.")

    def cargar_desde_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if ruta:
            with open(ruta, "rb") as f:
                self.foto_bytes = f.read()
            self.label_imagen.setPixmap(QPixmap(ruta).scaled(200, 200, Qt.KeepAspectRatio))

    def capturar_desde_camara(self):
        foto = camara.capturar_foto()
        if foto:
            self.foto_bytes = foto
            from PySide6.QtGui import QImage
            image = QImage.fromData(foto)
            self.label_imagen.setPixmap(QPixmap.fromImage(image).scaled(200, 200, Qt.KeepAspectRatio))

    