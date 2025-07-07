from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem
# from core import reportes  # backend con función ranking_ventas()

class RankingVentasDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📈 Ranking de productos vendidos")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Producto", "Código", "Cantidad vendida", "Total recaudado"])
        self.layout.addWidget(self.tabla)
        self.setLayout(self.layout)

    def cargar_datos(self):
        pass
        # datos = reportes.ranking_ventas()
        # self.tabla.setRowCount(len(datos))
        # for i, p in enumerate(datos):
        #     self.tabla.setItem(i, 0, QTableWidgetItem(p["nombre"]))
        #     self.tabla.setItem(i, 1, QTableWidgetItem(p["codigo_barra"]))
        #     self.tabla.setItem(i, 2, QTableWidgetItem(str(p["cantidad_vendida"])))
        #     self.tabla.setItem(i, 3, QTableWidgetItem(f"${p['total_recaudado']:.2f}"))
