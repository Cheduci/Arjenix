from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QDoubleSpinBox,
    QSpinBox, QPushButton, QFileDialog, QMessageBox, QComboBox, QHBoxLayout, 
    QSizePolicy, QInputDialog
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
        hbox_categoria = QHBoxLayout()
        self.categoria = QComboBox()
        btn_nueva_categoria = QPushButton("➕ Nueva")
        btn_nueva_categoria.clicked.connect(self.crear_categoria)
        hbox_categoria.addWidget(self.categoria)
        hbox_categoria.addWidget(btn_nueva_categoria)
        layout.addLayout(hbox_categoria)
        self.cargar_categorias()


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

        # Previsualización centrada
        self.label_imagen = QLabel("📷 Sin imagen")
        self.label_imagen.setAlignment(Qt.AlignCenter)
        self.label_imagen.setStyleSheet("""
            border: 1px solid #ccc;
            background-color: #fafafa;
            color: #888;
            font-style: italic;
        """)

        # 🪄 Estilo fluido y expandible
        self.label_imagen.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.label_imagen, stretch=1)

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

    def crear_categoria(self):
        nombre, ok = QInputDialog.getText(self, "Nueva categoría", "Nombre de la categoría:")
        if ok and nombre.strip():
            try:
                productos.crear_categoria(nombre.strip())
                self.cargar_categorias()  # recarga categorías en el combo
                self.categoria.setCurrentText(nombre.strip())
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo crear la categoría:\n{e}")

    def cargar_categorias(self):
        self.categoria.clear()
        categorias = productos.listar_categorias()
        self.categoria.addItems(categorias)


    def cargar_datos(self):
        producto = productos.obtener_producto_por_codigo(self.codigo)
        if not producto:
            QMessageBox.critical(self, "Error", "Producto no encontrado.")
            self.reject()
            return

        self.nombre.setText(producto["nombre"])


    def cargar_imagen(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if ruta:
            self.imagen_seleccionada = ruta
            self.label_imagen.setPixmap(QPixmap(ruta).scaled(200, 200, Qt.KeepAspectRatio))

    def aprobar_producto(self):
        nombre = self.nombre.text().strip().capitalize()
        descripcion = self.descripcion.toPlainText().strip().capitalize()
        categoria = self.categoria.currentText()
        precio_venta = self.precio_venta.value()

        if not all([nombre, descripcion, categoria]) or precio_venta <= 0:
            QMessageBox.warning(self, "Faltan datos", "Completá todos los campos obligatorios.")
            return
        
        # 📸 Imagen como binario
        foto = getattr(self, "foto_bytes", None)

        aprobado = productos.aprobar_producto(
            codigo=self.codigo,
            nombre=nombre,
            descripcion=descripcion,
            categoria=categoria,
            precio_venta=precio_venta,
            precio_compra=self.precio_compra.value(),
            stock_minimo=self.stock_minimo.value(),
            foto_bytes=foto
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

    