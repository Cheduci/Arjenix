from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QMessageBox, QHBoxLayout, QLabel, QSpinBox)
from PySide6.QtCore import Qt
from core.productos import obtener_productos_con_stock_bajo, ErrorStockBajo


class StockBajoDialog(QDialog):
    def __init__(self, sesion, parent=None):
        super().__init__(parent)
        self.sesion = sesion
        self.setWindowTitle("📉 Productos con stock bajo")
        self.resize(750, 450)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 🔎 Umbral dinámico
        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Umbral máximo de stock:"))
        self.umbral_input = QSpinBox()
        self.umbral_input.setMinimum(0)
        self.umbral_input.setMaximum(1000)
        self.umbral_input.setValue(0)  # 0 significa "usar stock_minimo registrado"
        filtro_layout.addWidget(self.umbral_input)

        self.btn_actualizar = QPushButton("🔄 Actualizar")
        self.btn_actualizar.clicked.connect(self.actualizar_tabla)
        filtro_layout.addWidget(self.btn_actualizar)

        layout.addLayout(filtro_layout)

        # 📋 Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Código", "Stock mínimo", "Stock actual", "Proveedor"])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.tabla)

        # Botón cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignRight)

        # 🔁 Carga inicial
        self.actualizar_tabla()

    def actualizar_tabla(self):
        try:
            umbral = self.umbral_input.value()
            productos = obtener_productos_con_stock_bajo(self.sesion, umbral if umbral > 0 else None)
        except ErrorStockBajo as e:
            QMessageBox.warning(self, "Error de consulta", str(e))
            self.tabla.setRowCount(0)
            return

        self.tabla.setRowCount(len(productos))
        for fila, p in enumerate(productos):
            self.tabla.setItem(fila, 0, QTableWidgetItem(p["nombre"]))
            self.tabla.setItem(fila, 1, QTableWidgetItem(p["codigo_barra"]))
            self.tabla.setItem(fila, 2, QTableWidgetItem(str(p["stock_minimo"] or 0)))
            self.tabla.setItem(fila, 3, QTableWidgetItem(str(p["stock_actual"])))

            proveedor = p.get("proveedor", "")
            proveedor_item = QTableWidgetItem(proveedor.strip())
            proveedor_item.setToolTip(proveedor)
            self.tabla.setItem(fila, 4, proveedor_item)

        self.tabla.sortItems(0)