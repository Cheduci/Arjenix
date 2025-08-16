from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QSizePolicy, QHBoxLayout, QDateEdit, QComboBox, QPushButton,
    QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
from bbdd.db_config import conectar_db
from dialogs.seleccionar_productos import SeleccionarProductosDialog
import csv
from datetime import datetime, timedelta
from core.productos import movimientos_exportables

class EstadisticasStockDialog(QDialog):
    def __init__(self, sesion):
        super().__init__()
        self.sesion = sesion
        self.codigos_seleccionados = []
        self.setWindowTitle("📈 Estadísticas de stock")
        self.setMinimumSize(720, 520)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 🎯 Encabezado
        titulo = QLabel("📈 Panel de estadísticas")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 12px;")
        layout.addWidget(titulo)

        # 📅 Filtros superiores
        filtros_layout = QHBoxLayout()

        # Fechas
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_fin = QDateEdit()
        self.fecha_fin.setDate(QDate.currentDate())
        self.fecha_fin.setCalendarPopup(True)

        filtros_layout.addWidget(QLabel("Desde:"))
        filtros_layout.addWidget(self.fecha_inicio)
        filtros_layout.addWidget(QLabel("Hasta:"))
        filtros_layout.addWidget(self.fecha_fin)

        # Tipo de análisis
        self.tipo_selector = QComboBox()
        self.tipo_selector.addItems([
            "Productos con más reposiciones",
            "Frecuencia promedio por producto",
            "Reposiciones vs Ventas",
            "Actividad por usuario",
            "Alertas de reposición",
            "Movimientos detallados"
        ])
        filtros_layout.addWidget(QLabel("Análisis:"))
        filtros_layout.addWidget(self.tipo_selector)

        # Botón para elegir productos
        self.btn_selector = QPushButton("🎯 Seleccionar productos")
        self.btn_selector.clicked.connect(self.abrir_selector_productos)
        filtros_layout.addWidget(self.btn_selector)

        layout.addLayout(filtros_layout)

        # 📋 Tabla de resultados
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(1)
        self.tabla.setHorizontalHeaderLabels(["Resultado"])
        layout.addWidget(self.tabla)

        # 📤 Botón de exportación
        export_layout = QHBoxLayout()
        self.btn_exportar_csv = QPushButton("Exportar a CSV")
        self.btn_exportar_csv.clicked.connect(self.exportar_a_csv)
        export_layout.addStretch()
        export_layout.addWidget(self.btn_exportar_csv)
        layout.addLayout(export_layout)

        # 🔍 Etiqueta de productos seleccionados
        self.productos_label = QLabel()
        self.productos_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.productos_label)

        # ✅ Conexión de señales (Punto 3)
        self.btn_actualizar = QPushButton()
        self.tipo_selector.currentIndexChanged.connect(self.actualizar_resultados)
        self.btn_actualizar.clicked.connect(self.actualizar_resultados)

        self.setLayout(layout)

    def abrir_selector_productos(self):
        dlg = SeleccionarProductosDialog(self.sesion, modo="estadistica")
        if dlg.exec():
            self.codigos_seleccionados = dlg.obtener_codigos_seleccionados()
            nombres = dlg.obtener_nombres_seleccionados()
            self.productos_label.setText(f"🔍 Productos seleccionados: {', '.join(nombres)}")
            print("Codigos seleccionados:", self.codigos_seleccionados)

            self.actualizar_resultados()


    def actualizar_resultados(self):
        tipo = self.tipo_selector.currentText()

        if tipo == "Productos con más reposiciones":
            datos = self.productos_con_mas_reposiciones()
        elif tipo == "Frecuencia promedio por producto":
            datos = self.frecuencia_promedio_por_producto()
        elif tipo == "Reposiciones vs Ventas":
            datos = self.reposiciones_vs_ventas()
        elif tipo == "Actividad por usuario":
            datos = self.actividad_por_usuario()
        elif tipo == "Alertas de reposición":
            datos = self.alertas_reposicion()
        elif tipo == "Movimientos detallados":
            datos_completos = self.resumen_por_producto(
                self.fecha_inicio.date().toString("yyyy-MM-dd"),
                self.fecha_fin.date().toString("yyyy-MM-dd"),
                self.codigos_seleccionados
            )

            # 🔍 Filtrar solo las columnas deseadas para la tabla
            columnas_preview = ["Producto", "Código", "Total Vendido", "Total Repuesto", "Stock Actual", "Último Movimiento"]
            datos = []

            for fila in datos_completos:
                preview = {col: fila.get(col, "—") for col in columnas_preview}
                datos.append(preview)
        else:
            datos = []

        self.mostrar_en_tabla(datos)

    def mostrar_en_tabla(self, datos):
        if not datos:
            self.tabla.setRowCount(0)
            self.tabla.setColumnCount(1)
            self.tabla.setHorizontalHeaderLabels(["Sin datos"])
            return

        columnas = list(datos[0].keys())
        self.tabla.setColumnCount(len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setRowCount(len(datos))

        for fila, registro in enumerate(datos):
            for col, clave in enumerate(columnas):
                valor = str(registro.get(clave, "—"))
                self.tabla.setItem(fila, col, QTableWidgetItem(valor))
                
    def exportar_a_csv(self):
        tipo = self.tipo_selector.currentText()

        # Obtener datos según tipo de análisis
        if tipo == "Productos con más reposiciones":
            datos = self.productos_con_mas_reposiciones()
        elif tipo == "Frecuencia promedio por producto":
            datos = self.frecuencia_promedio_por_producto()
        elif tipo == "Reposiciones vs Ventas":
            datos = self.reposiciones_vs_ventas()
            # 🧠 Generar columna "Alerta" basada en ratio
            for fila in datos:
                ratio = fila.get("Ratio Venta/Reposición", 0)
                if ratio < 1:
                    fila["Alerta"] = "🟡 Reposición superior a ventas"
                elif ratio > 3:
                    fila["Alerta"] = "🟢 Alta rotación"
                else:
                    fila["Alerta"] = "⚪ Equilibrado"
        elif tipo == "Actividad por usuario":
            datos = self.actividad_por_usuario()
        elif tipo == "Alertas de reposición":
            datos = self.alertas_reposicion()
        elif tipo == "Movimientos detallados":
            datos, movimientos = self.movimientos_detallados(
                self.fecha_inicio.date().toString("yyyy-MM-dd"),
                self.fecha_fin.date().toString("yyyy-MM-dd"),
                self.codigos_seleccionados,
                tipo="Ambos"
            )
            # 🧾 Elegir qué exportar: versión completa
            datos = movimientos

            # 🧼 Formatear fechas si es datetime
            for fila in datos:
                if isinstance(fila.get("fecha"), datetime):
                    fila["fecha"] = fila["fecha"].strftime("%Y-%m-%d %H:%M")
        else:
            datos = []

        # ✅ Validación: ¿hay datos válidos?
        if not datos or not isinstance(datos[0], dict):
            QMessageBox.information(self, "Exportación", "No hay datos válidos para exportar.")
            return

        # ✅ Validación: todas las columnas consistentes
        columnas = list(datos[0].keys())
        for fila in datos:
            if set(fila.keys()) != set(columnas):
                QMessageBox.warning(self, "Error de exportación", "Las columnas no son consistentes entre los datos.")
                return

        # 📁 Nombre de archivo sugerido con timestamp
        nombre_default = f"{tipo.replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d')}.csv"
        nombre_archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar como CSV",
            nombre_default,
            "Archivos CSV (*.csv)"
        )

        if not nombre_archivo:
            return  # Cancelado por el usuario

        # 🧾 Exportar archivo
        try:
            with open(nombre_archivo, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=columnas, delimiter=";")
                writer.writeheader()
                writer.writerows(datos)

            QMessageBox.information(self, "Exportación exitosa", f"Datos guardados en:\n{nombre_archivo}")

        except Exception as e:
            QMessageBox.warning(self, "Error al exportar", f"No se pudo guardar el archivo:\n{e}")

    def productos_con_mas_reposiciones(self, top_n=10):
    # Simulación temporal (hasta conectar con la DB)
        return [
            {"Producto": "Yerba mate", "Reposiciones": 18},
            {"Producto": "Harina", "Reposiciones": 15},
            {"Producto": "Aceite", "Reposiciones": 14},
            {"Producto": "Fideos", "Reposiciones": 13},
            {"Producto": "Galletitas", "Reposiciones": 11},
            {"Producto": "Sal", "Reposiciones": 10},
            {"Producto": "Azúcar", "Reposiciones": 10},
            {"Producto": "Leche", "Reposiciones": 9},
            {"Producto": "Arroz", "Reposiciones": 9},
            {"Producto": "Salsa de tomate", "Reposiciones": 8}
        ]

    def frecuencia_promedio_por_producto(self):
    # Simulación temporal con datos ficticios
        return [
            {"Producto": "Leche", "Frecuencia promedio (días)": 3.2},
            {"Producto": "Yerba mate", "Frecuencia promedio (días)": 2.6},
            {"Producto": "Aceite", "Frecuencia promedio (días)": 4.0},
            {"Producto": "Fideos", "Frecuencia promedio (días)": 5.1},
            {"Producto": "Arroz", "Frecuencia promedio (días)": 6.7},
            {"Producto": "Sal", "Frecuencia promedio (días)": 7.0}
        ]

    def reposiciones_vs_ventas(self):
    # Datos ficticios para probar la tabla y exportación
        return [
            {"Producto": "Leche", "Reposiciones": 12, "Ventas": 38, "Ratio Venta/Reposición": 3.17},
            {"Producto": "Yerba mate", "Reposiciones": 15, "Ventas": 30, "Ratio Venta/Reposición": 2.00},
            {"Producto": "Aceite", "Reposiciones": 20, "Ventas": 18, "Ratio Venta/Reposición": 0.90},
            {"Producto": "Harina", "Reposiciones": 10, "Ventas": 7, "Ratio Venta/Reposición": 0.70},
            {"Producto": "Fideos", "Reposiciones": 5, "Ventas": 25, "Ratio Venta/Reposición": 5.00}
        ]

    def actividad_por_usuario(self):
    # Datos ficticios para testear exportación y tabla
        return [
            {"Usuario": "carlos", "Reposiciones realizadas": 34},
            {"Usuario": "florencia", "Reposiciones realizadas": 28},
            {"Usuario": "lucas", "Reposiciones realizadas": 15},
            {"Usuario": "sistema", "Reposiciones realizadas": 10}
        ]

    def alertas_reposicion(self):
    # Datos ficticios para testeo
        return [
            {"Producto": "Aceite", "Frecuencia promedio (días)": 0.9, "Alerta": "🔴 Reposición excesiva"},
            {"Producto": "Arroz", "Frecuencia promedio (días)": 9.0, "Alerta": "🟡 Intervalo irregular"},
            {"Producto": "Sal", "Frecuencia promedio (días)": 14.5, "Alerta": "🔵 Ausencia prolongada"},
            {"Producto": "Leche", "Frecuencia promedio (días)": 2.1, "Alerta": "🟢 Frecuencia normal"},
            {"Producto": "Fideos", "Frecuencia promedio (días)": 6.3, "Alerta": "⚪ Sin anomalías"}
        ]

    def movimientos_detallados(self, fecha_inicio, fecha_fin, codigos, tipo="Ambos"):
        # Llamada a la función de exportación de movimientos
        fecha_fin_extendida = fecha_fin + timedelta(days=1)
        movimientos, error = movimientos_exportables(fecha_inicio, fecha_fin_extendida, codigos, tipo)

        if movimientos is None:
            QMessageBox.warning(self, "Error", f"No se pudieron obtener los movimientos: {error}")
            return [], []

        # Simplificar para mostrar en tabla
        datos = []
        for mov in movimientos:
            datos.append({
                "Fecha": mov["fecha"].strftime("%Y-%m-%d %H:%M"),
                "Producto": mov["nombre"],
                "Código": mov["codigo_barra"],
                "Tipo": mov["tipo_movimiento"],
                "Cantidad": mov["cantidad"],
                "Usuario": mov["usuario"] or "—"
            })

        return datos, movimientos

    def resumen_por_producto(self, fecha_inicio, fecha_fin, codigos):
        if isinstance(fecha_fin, str):
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
        fecha_fin_extendida = fecha_fin + timedelta(days=1)
        movimientos, error = movimientos_exportables(fecha_inicio, fecha_fin_extendida, codigos, tipo="Ambos")

        if movimientos is None:
            QMessageBox.warning(self, "Error", f"No se pudieron obtener los movimientos: {error}")
            return []

        resumen = {}
        for mov in movimientos:
            cod = mov["codigo_barra"]
            if cod not in resumen:
                resumen[cod] = {
                    "Producto": mov["nombre"],
                    "Código": cod,
                    "Total Vendido": 0,
                    "Total Repuesto": 0,
                    "Stock Actual": mov["stock_actual"],
                    "Último Movimiento": mov["fecha"]
                }

            if mov["tipo_movimiento"] == "Venta":
                resumen[cod]["Total Vendido"] += abs(mov["cantidad"])
            elif mov["tipo_movimiento"] == "Reposición":
                resumen[cod]["Total Repuesto"] += mov["cantidad"]

            # Actualizar stock actual y fecha si es más reciente
            if mov["fecha"] > resumen[cod]["Último Movimiento"]:
                resumen[cod]["Stock Actual"] = mov["stock_actual"]
                resumen[cod]["Último Movimiento"] = mov["fecha"]

        # Formatear para tabla
        datos = []
        for r in resumen.values():
            datos.append({
                "Producto": r["Producto"],
                "Código": r["Código"],
                "Total Vendido": r["Total Vendido"],
                "Total Repuesto": r["Total Repuesto"],
                "Stock Actual": r["Stock Actual"],
                "Último Movimiento": r["Último Movimiento"].strftime("%Y-%m-%d %H:%M")
            })

        return datos
