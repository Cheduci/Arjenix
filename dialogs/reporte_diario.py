from PySide6.QtWidgets import (QDialog, QVBoxLayout, QGroupBox, QHBoxLayout, QDateEdit, QLabel,
            QTableWidget, QPushButton, QTableWidgetItem, QMessageBox)
from PySide6.QtCore import QDate
from core.ventas import consultar_reporte_diario
import csv
import os
from datetime import datetime, timedelta


class ReporteDiarioDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Reporte de ganancias")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.resultados_actuales = []


    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Fecha desde/hasta
        fechas_group = QGroupBox("📅 Selección de período")
        fechas_layout = QHBoxLayout()

        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setDate(QDate.currentDate().addDays(-1))

        self.fecha_fin = QDateEdit()
        self.fecha_fin.setCalendarPopup(True)
        self.fecha_fin.setDate(QDate.currentDate())

        fechas_layout.addWidget(QLabel("Desde:"))
        fechas_layout.addWidget(self.fecha_inicio)
        fechas_layout.addWidget(QLabel("Hasta:"))
        fechas_layout.addWidget(self.fecha_fin)

        fechas_group.setLayout(fechas_layout)
        layout.addWidget(fechas_group)

        # Resultado
        self.tabla_resultado = QTableWidget(0, 4)
        self.tabla_resultado.setHorizontalHeaderLabels(["Fecha", "Producto", "Cantidad", "Venta total", "Ganancia"])
        layout.addWidget(self.tabla_resultado)

        # Botones
        btn_generar = QPushButton("📊 Generar reporte")
        btn_generar.clicked.connect(self.generar_reporte)
        layout.addWidget(btn_generar)

        btn_exportar = QPushButton("💾 Exportar a CSV")
        btn_exportar.clicked.connect(self.exportar_csv)
        layout.addWidget(btn_exportar)

    def generar_reporte(self):
        fecha_ini = self.fecha_inicio.date().toPython()
        fecha_fin = self.fecha_fin.date().toPython()
        fecha_fin_extendida = fecha_fin + timedelta(days=1)

        self.resultados_actuales = consultar_reporte_diario(fecha_ini, fecha_fin_extendida)
        self.tabla_resultado.setRowCount(0)

        for fila in self.resultados_actuales:
            fecha_hora, nombre, cantidad, venta_total, ganancia = fila
            fila_idx = self.tabla_resultado.rowCount()
            self.tabla_resultado.insertRow(fila_idx)
            self.tabla_resultado.setItem(fila_idx, 0, QTableWidgetItem(str(fecha_hora.date())))
            self.tabla_resultado.setItem(fila_idx, 1, QTableWidgetItem(nombre))
            self.tabla_resultado.setItem(fila_idx, 2, QTableWidgetItem(str(cantidad)))
            self.tabla_resultado.setItem(fila_idx, 3, QTableWidgetItem(f"${venta_total:.2f}"))
            self.tabla_resultado.setItem(fila_idx, 4, QTableWidgetItem(f"${ganancia:.2f}"))

    def exportar_csv(self):
        self.generar_reporte()

        if not self.resultados_actuales:
            QMessageBox.warning(self, "Sin datos", "Generá primero el reporte antes de exportar.")
            return
        
        # 🗃️ Exportar a CSV
        carpeta = os.path.join("exportaciones", "reportes")
        os.makedirs(carpeta, exist_ok=True)

        fecha_texto = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nombre_archivo = os.path.join(carpeta, f"reporte_{fecha_texto}.csv")
        usuario = self.parent().sesion.get("username")

        try:
            with open(nombre_archivo, mode="w", newline="", encoding="utf-8") as archivo:
                writer = csv.writer(archivo)

                # 🧠 Metadatos
                writer.writerow([f"# Generado por: {usuario} | Fecha de exportación: {fecha_texto}"])

                # Encabezado de datos
                writer.writerow(["Fecha", "Hora", "Producto", "Cantidad", "Venta total", "Ganancia"])
                for fila in self.resultados_actuales:
                    fecha_hora, nombre, cantidad, venta_total, ganancia = fila
                    writer.writerow([
                        fecha_hora.date(), 
                        fecha_hora.time().strftime("%H:%M:%S"), 
                        nombre, 
                        cantidad, 
                        f"{venta_total:.2f}", 
                        f"{ganancia:.2f}"
                    ])
            QMessageBox.information(
                self, "✅ Reporte guardado",
                f"El reporte fue exportado como CSV:\n{nombre_archivo}"
            )
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"No se pudo exportar el archivo:\n{e}")