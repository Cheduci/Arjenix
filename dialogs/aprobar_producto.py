from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QDoubleSpinBox,
    QSpinBox, QPushButton, QFileDialog, QMessageBox, QComboBox, QHBoxLayout, 
    QSizePolicy, QInputDialog
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from core import productos
from modulos import camara
from helpers.dialogos import obtener_codigo
from typing import Literal

class AprobarProductoDialog(QDialog):
    def __init__(self, sesion: dict, config_sistema: dict, codigo: str):
        super().__init__()
        self.sesion = sesion
        self.config_sistema = config_sistema
        self.codigo = codigo
        self.setWindowTitle("✅ Aprobar producto")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.cargar_datos()
        self.codigo_confirmado = None

    def setup_ui(self):
        layout_principal = QHBoxLayout()

        layout_formulario = QVBoxLayout()


        # 🔤 Nombre
        layout_formulario.addWidget(QLabel("Nombre:"))
        self.nombre = QLineEdit()
        layout_formulario.addWidget(self.nombre)

        # 📝 Descripción
        layout_formulario.addWidget(QLabel("Descripción:"))
        self.descripcion = QTextEdit()
        self.descripcion.setMaximumHeight(60)  # Puedes ajustar este valor según prefieras
        layout_formulario.addWidget(self.descripcion)

        # 🏷️ Categoría
        layout_formulario.addWidget(QLabel("Categoría:"))
        hbox_categoria = QHBoxLayout()
        self.categoria = QComboBox()
        btn_nueva_categoria = QPushButton("➕ Nueva")
        btn_nueva_categoria.clicked.connect(self.crear_categoria)
        hbox_categoria.addWidget(self.categoria)
        hbox_categoria.addWidget(btn_nueva_categoria)
        layout_formulario.addLayout(hbox_categoria)
        self.cargar_categorias()
        
        # Agrupar horizontalmente precio de compra, precio de venta y stock mínimo
        hbox_precios_stock = QHBoxLayout()
        
        # 💰 Precio de compra
        vbox_compra = QVBoxLayout()
        vbox_compra.addWidget(QLabel("Precio de compra:"))
        self.precio_compra = QDoubleSpinBox()
        self.precio_compra.setPrefix("$")
        self.precio_compra.setMaximum(999999999)
        self.precio_compra.setDecimals(2)
        vbox_compra.addWidget(self.precio_compra)
        hbox_precios_stock.addLayout(vbox_compra)
        
        # 💸 Precio de venta
        vbox_venta = QVBoxLayout()
        vbox_venta.addWidget(QLabel("Precio de venta:"))
        self.precio_venta = QDoubleSpinBox()
        self.precio_venta.setPrefix("$")
        self.precio_venta.setMaximum(999999999)
        self.precio_venta.setDecimals(2)
        vbox_venta.addWidget(self.precio_venta)
        hbox_precios_stock.addLayout(vbox_venta)
        
        # 📦 Stock mínimo
        vbox_stock = QVBoxLayout()
        vbox_stock.addWidget(QLabel("Stock mínimo:"))
        self.stock_minimo = QSpinBox()
        self.stock_minimo.setRange(0, 1000000)
        vbox_stock.addWidget(self.stock_minimo)
        hbox_precios_stock.addLayout(vbox_stock)
        
        # Agregar el layout horizontal al layout principal
        layout_formulario.addLayout(hbox_precios_stock)
        

        # 🖼️ Imagen del producto
        layout_formulario.addWidget(QLabel("Imagen del producto:"))

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
        layout_formulario.addWidget(self.label_imagen, stretch=1)

        # 🎛️ Botones: Examinar y Capturar
        hbox_foto = QHBoxLayout()
        self.btn_examinar = QPushButton("📁 Examinar")
        self.btn_capturar = QPushButton("📸 Capturar")
        self.btn_examinar.clicked.connect(self.cargar_desde_archivo)
        self.btn_capturar.clicked.connect(self.capturar_desde_camara)
        hbox_foto.addWidget(self.btn_examinar)
        hbox_foto.addWidget(self.btn_capturar)
        layout_formulario.addLayout(hbox_foto)

        # ✅ Botón aprobar
        layout_formulario.addStretch()
        self.btn_aprobar = QPushButton("✅ Aprobar producto")
        self.btn_aprobar.clicked.connect(self.aprobar_producto)
        layout_formulario.addWidget(self.btn_aprobar)


        # 🔍 Barra lateral para ingreso de código
        layout_lateral = QVBoxLayout()

        self.label_codigo_confirmado = QLabel(f"🆔 Código actual: {self.codigo}")
        self.label_codigo_confirmado.setStyleSheet("font-weight: bold; color: #333; padding: 4px;")

        botones = QHBoxLayout()
        self.btn_escanear = QPushButton("📷 Escanear")
        self.btn_manual = QPushButton("✍️ Ingresar")
        # Conexiones usando lambdas para pasar `self` como parent
        self.btn_manual.clicked.connect(lambda: self._manejar_codigo("manual"))
        self.btn_escanear.clicked.connect(lambda: self._manejar_codigo("escanear"))

        botones.addWidget(self.btn_escanear)
        botones.addWidget(self.btn_manual)

        layout_lateral.addWidget(self.label_codigo_confirmado)
        layout_lateral.addSpacing(10)
        layout_lateral.addLayout(botones)
        layout_lateral.addStretch()


        layout_principal.addLayout(layout_formulario, stretch=3)
        if self.config_sistema.get("modo_codigo_barra") != "auto":
            layout_principal.addLayout(layout_lateral, stretch=1)
        self.setLayout(layout_principal)

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
        modo = self.config_sistema.get("modo_codigo_barra", "mixto")

        if modo not in {"auto", "manual", "mixto"}:
            QMessageBox.critical(self, "Error de configuración", "⚠️ El modo de código de barra no está definido correctamente.")
            return
        
        if self.codigo_confirmado is not None:
            self.codigo = self.codigo_confirmado
            
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
            image = QImage.fromData(foto)
            self.label_imagen.setPixmap(QPixmap.fromImage(image).scaled(200, 200, Qt.KeepAspectRatio))

    def _manejar_codigo(self, modo: Literal["manual", "escanear"]):
        codigo = obtener_codigo(self, modo, self.codigo_confirmado)
        if codigo:
            self.codigo_confirmado = codigo
            self.label_codigo_confirmado.setText(f"🆔 Código: {codigo}")

