from PySide6.QtWidgets import (QDialog, QVBoxLayout, QGroupBox, QHBoxLayout, QDateEdit, QLabel,
            QTableWidget, QPushButton, QTableWidgetItem, QMessageBox)
from PySide6.QtCore import QDate
from core.ventas import consultar_reporte_diario
import subprocess
import platform
import os
from datetime import timedelta
from helpers.exportar import exportar_pdf_diario, exportar_csv_reporte_diario


class ReporteDiarioDialog(QDialog):
    def __init__(self, sesion, parent=None):
        super().__init__(parent)
        self.sesion = sesion
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

        boton_exportar_csv = QPushButton("Exportar CSV")
        boton_exportar_pdf = QPushButton("Exportar PDF")

        boton_exportar_csv.clicked.connect(self.exportar_csv)
        boton_exportar_pdf.clicked.connect(self.exportar_pdf)

        layout_botones = QHBoxLayout()
        layout_botones.addWidget(boton_exportar_csv)
        layout_botones.addWidget(boton_exportar_pdf)
        layout.addLayout(layout_botones)

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
        
        try:
            ruta = exportar_csv_reporte_diario(self.resultados_actuales, self.sesion)
            QMessageBox.information(self, "✅ Reporte guardado", f"El reporte fue exportado como CSV:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"No se pudo exportar el archivo:\n{e}")

    def exportar_pdf(self):
        self.generar_reporte()

        if not self.resultados_actuales:
            QMessageBox.warning(self, "Sin datos", "Generá primero el reporte antes de exportar.")
            return

        try:
            ruta = exportar_pdf_diario(self.resultados_actuales, self.sesion)
             # 🔓 Intentamos abrir el archivo
            try:
                if platform.system() == "Windows":
                    os.startfile(ruta)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.call(["open", ruta])
                else:  # Linux o similares
                    subprocess.call(["xdg-open", ruta])
            except Exception as e:
                QMessageBox.warning(self, "PDF generado", f"El archivo fue exportado, pero no se pudo abrir automáticamente.\nRuta:\n{ruta}")

            QMessageBox.information(self, "✅ Reporte guardado", f"El reporte fue exportado como PDF:\n{ruta}")
        
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"No se pudo exportar el archivo:\n{e}")

