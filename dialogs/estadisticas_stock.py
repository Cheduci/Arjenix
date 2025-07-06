# modulos/estadisticas_stock.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QSizePolicy
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
from bbdd.db_config import conectar_db

class EstadisticasStockDialog(QDialog):
    def __init__(self, sesion):
        super().__init__()
        self.sesion = sesion
        self.setWindowTitle("📈 Estadísticas de stock")
        self.setMinimumSize(640, 480)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🧮 Productos más repuestos"))

        tabla = self.cargar_tabla()
        layout.addWidget(tabla)

        grafico = self.generar_grafico()
        layout.addWidget(grafico)

        self.setLayout(layout)

    def cargar_tabla(self):
        tabla = QTableWidget()
        tabla.setColumnCount(2)
        tabla.setHorizontalHeaderLabels(["Producto", "Veces repuesto"])
        tabla.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        conn = conectar_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.nombre, COUNT(r.id) as cantidad
            FROM productos p
            JOIN reposiciones r ON p.id = r.producto_id
            GROUP BY p.nombre
            ORDER BY cantidad DESC
            LIMIT 5;
        """)
        resultados = cur.fetchall()
        conn.close()

        tabla.setRowCount(len(resultados))
        for i, (nombre, cantidad) in enumerate(resultados):
            tabla.setItem(i, 0, QTableWidgetItem(nombre))
            tabla.setItem(i, 1, QTableWidgetItem(str(cantidad)))

        return tabla

    def generar_grafico(self):
        fig = Figure(figsize=(5, 2.5))
        ax = fig.add_subplot(111)

        conn = conectar_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.nombre, COUNT(r.id) as cantidad
            FROM productos p
            JOIN reposiciones r ON p.id = r.producto_id
            GROUP BY p.nombre
            ORDER BY cantidad DESC
            LIMIT 5;
        """)
        resultados = cur.fetchall()
        conn.close()

        nombres = [r[0] for r in resultados]
        cantidades = [r[1] for r in resultados]

        ax.bar(nombres, cantidades, color="#3e7bb6")
        ax.set_title("Top 5 productos más repuestos")
        ax.tick_params(axis='x', rotation=30)

        canvas = Canvas(fig)
        return canvas
