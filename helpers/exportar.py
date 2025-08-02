from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile
import barcode
from barcode.writer import ImageWriter
import webbrowser
from datetime import datetime, timedelta
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm
from collections import defaultdict
import os, csv
from core.configuracion import obtener_config_empresa
from reportlab.lib import colors
from pathlib import Path

documentos = Path.home() / "Documents"
directorio = documentos / "Exportaciones Arjenix"

def exportar_credenciales_basicas(nombre_archivo, usuario: str, password: str, rol: str = "dueño"):
    carpeta = os.path.dirname(nombre_archivo)
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    
    c = canvas.Canvas(nombre_archivo, pagesize=A4)
    c.setTitle("Credenciales iniciales — Arjenix")

    x = 80
    y = 760
    espacio = 32

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "🔐 Credenciales iniciales de acceso")
    y -= espacio * 2

    c.setFont("Helvetica", 12)
    c.drawString(x, y, f"👤 Usuario: {usuario}")
    y -= espacio
    c.drawString(x, y, f"🗝️ Contraseña: {password}")
    y -= espacio
    c.drawString(x, y, f"🛡️ Rol: {rol}")

    y -= espacio * 2
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(x, y, "Este archivo fue generado automáticamente al configurar Arjenix.")

    c.save()

def exportar_codigo_pdf(nombre, codigo, precio, cantidad):
    try:
        cantidad = int(cantidad)
        if cantidad <= 0:
            print("⚠️ La cantidad debe ser mayor a cero.")
            return

        # Dimensiones
        etiquetas_por_fila = 5
        etiquetas_por_columna = 8
        max_etiquetas = etiquetas_por_fila * etiquetas_por_columna  # 40 por hoja
        etiquetas_a_imprimir = min(cantidad, max_etiquetas)

        # Generar código de barras como imagen PNG temporal
        tmp_path_base = tempfile.mktemp()
        ean = barcode.get('ean13', codigo, writer=ImageWriter())
        imagen_path = ean.save(tmp_path_base)

        # Preparar PDF
        directorio = os.path.join(os.getcwd(), "exportaciones", "etiquetas")
        os.makedirs(directorio, exist_ok=True)

        pdf_path = os.path.join(directorio, f"etiquetas_{codigo}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A4)
        pagina_ancho, pagina_alto = A4

        margen_izq = 40
        margen_sup = 60
        espaciado_x = 100
        espaciado_y = 60

        for i in range(etiquetas_a_imprimir):
            fila = i // etiquetas_por_fila
            col = i % etiquetas_por_fila
            x = margen_izq + col * espaciado_x
            y = pagina_alto - margen_sup - fila * espaciado_y

            c.drawInlineImage(imagen_path, x, y + 3, width=80, height=30)  # Imagen primero, Más arriba

            c.setFont("Helvetica", 8)
            c.drawString(x, y - 3, nombre[:25])  # Más separado hacia abajo del código
            # c.drawString(x, y - 15, f"${precio:.2f}")



        c.showPage()
        c.save()

        os.remove(imagen_path)
        webbrowser.open(pdf_path)
        print(f"✅ PDF generado: {pdf_path}")

        if cantidad > etiquetas_a_imprimir:
            print(f"ℹ️ Se generó una hoja con {etiquetas_a_imprimir}. Podés imprimir {cantidad // etiquetas_a_imprimir} copias para cubrir la cantidad deseada.")

    except Exception as e:
        print(f"❌ Error al generar etiquetas: {e}")

def exportar_csv_reporte_diario(resultados, sesion):

    carpeta = os.path.join("exportaciones", "reportes")
    os.makedirs(carpeta, exist_ok=True)

    fecha_texto = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_archivo = os.path.join(carpeta, f"reporte_{fecha_texto}.csv")
    usuario = sesion.get("username", "desconocido")

    with open(nombre_archivo, mode="w", newline="", encoding="utf-8") as archivo:
        writer = csv.writer(archivo)
        writer.writerow([f"# Generado por: {usuario} | Fecha de exportación: {fecha_texto}"])
        writer.writerow(["Fecha", "Hora", "Producto", "Cantidad", "Venta total", "Ganancia"])
        for fecha_hora, nombre, cantidad, venta_total, ganancia in resultados:
            writer.writerow([
                fecha_hora.date(),
                fecha_hora.time().strftime("%H:%M:%S"),
                nombre,
                cantidad,
                f"{venta_total:.2f}",
                f"{ganancia:.2f}"
            ])

    return nombre_archivo

def agrupar_por_producto(resultados):
    agrupado = defaultdict(lambda: {"cantidad": 0, "venta": 0, "ganancia": 0})
    for fila in resultados:
        producto = fila[1]  # nombre
        cantidad = fila[2]
        venta_total = fila[3]
        ganancia = fila[4]

        agrupado[producto]["cantidad"] += cantidad
        agrupado[producto]["venta"] += venta_total
        agrupado[producto]["ganancia"] += ganancia

    return agrupado

def exportar_pdf_diario(resultados, sesion):
    # Crear ruta completa
    carpeta = directorio / "reportes"
    carpeta.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    usuario = sesion.get("username", "desconocido")
    nombre_archivo = f"reporte_diario_{timestamp}_{usuario}.pdf"
    ruta = carpeta / nombre_archivo

    # 📥 Datos de configuración
    config_empresa = obtener_config_empresa()
    fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")

    c = canvas.Canvas(ruta, pagesize=A4)
    ancho, alto = A4

    # Agrupamos resultados por fecha
    agrupado = defaultdict(list)
    for fila in resultados:
        fecha = fila[0].date()
        agrupado[fecha].append(fila)

    for fecha, items in sorted(agrupado.items(), reverse=True):
        # Encabezado institucional (logo, nombre, fecha)
        dibujar_encabezado(c, config_empresa, fecha)

        y = alto - 120  # posición inicial
        # c.setFont("Helvetica-Bold", 12)
        # c.drawString(50, y, f"🗓 Fecha: {fecha}")
        # y -= 20
        # c.drawString(50, y, "Artículos vendidos:")
        # y -= 25

        # Dibujamos cada producto vendido
        dibujar_contenido_del_dia(c, items, fecha)

        # Pie institucional
        dibujar_pie_de_pagina(c)

        c.showPage()

    c.save()
    return ruta


def dibujar_encabezado(canvas, datos_empresa, fecha):
    ancho, alto = A4
    margen_izq = 50
    margen_sup = alto - 50

    # Logo
    if datos_empresa.get('logo'):
        # Logo binario (guardamos temporalmente si existe)
        logo_binario = datos_empresa.get('logo')
        if logo_binario:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp:
                    temp.write(logo_binario)
                    ruta_temporal = temp.name

                canvas.drawImage(
                    ImageReader(ruta_temporal),
                    margen_izq, margen_sup - 40,
                    width=60, height=40,
                    preserveAspectRatio=True, mask='auto'
                )

                os.remove(ruta_temporal)  # eliminamos el archivo temporal
            except Exception as e:
                print(f"⚠️ Error al cargar logo desde binario: {e}")

    # Nombre de empresa y slogan
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(margen_izq + 70, margen_sup - 10, datos_empresa.get('nombre', ''))
    canvas.setFont("Helvetica-Oblique", 10)
    canvas.drawString(margen_izq + 70, margen_sup - 25, datos_empresa.get('slogan', ''))

    # Fecha de generación
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(ancho - 50, margen_sup - 10, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

def dibujar_pie_de_pagina(canvas):
    ancho, alto = A4
    margen_inf = 40

    # Línea de separación
    canvas.setStrokeColorRGB(0.6, 0.6, 0.6)
    canvas.setLineWidth(0.5)
    canvas.line(50, margen_inf + 15, ancho - 50, margen_inf + 15)

    # Texto del pie
    canvas.setFont("Helvetica", 8)
    canvas.setFillColorRGB(0.3, 0.3, 0.3)
    canvas.drawString(50, margen_inf, "Este informe es confidencial y de uso interno.")
    canvas.drawRightString(ancho - 50, margen_inf, f"Página {canvas.getPageNumber()}")
    
def dibujar_contenido_del_dia(canvas, items, fecha):
    ancho, alto = A4
    y = alto - 120

    # Encabezado de fecha y sección
    canvas.setFont("Helvetica-Bold", 12)
    canvas.setFillColor(colors.darkblue)
    canvas.drawString(50, y, f"Fecha: {fecha}")
    y -= 20
    canvas.drawString(50, y, "Artículos vendidos:")
    y -= 25

    # Títulos de tabla
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.white)
    canvas.setFillColorRGB(0.4, 0.6, 0.8)  # azul suave
    canvas.rect(50, y - 2, 500, 15, fill=True, stroke=False)
    canvas.setFillColor(colors.white)
    canvas.drawString(60, y, "Producto")
    canvas.drawString(220, y, "Cant.")
    canvas.drawString(270, y, "Venta")
    canvas.drawString(340, y, "Ganancia")
    y -= 15

    canvas.setStrokeColor(colors.grey)
    canvas.line(50, y, 550, y)
    y -= 10

    agrupados = agrupar_por_producto(items)

    # Filas de productos
    canvas.setFont("Helvetica", 10)
    total_cant = total_venta = total_ganancia = 0

    for i, (producto, datos) in enumerate(agrupados.items()):
        if i % 2 == 0:
            canvas.setFillColorRGB(0.95, 0.95, 1)  # fondo azul claro
            canvas.rect(50, y - 2, 500, 15, fill=True, stroke=False)

        canvas.setFillColor(colors.black)
        canvas.drawString(60, y, producto)  # nombre
        canvas.drawRightString(260, y, str(datos["cantidad"]))
        canvas.drawRightString(330, y, f"${datos['venta']:.2f}")
        canvas.drawRightString(400, y, f"${datos['ganancia']:.2f}")

        total_cant += datos["cantidad"]
        total_venta += datos["venta"]
        total_ganancia += datos["ganancia"]
        y -= 15

        if y < 100:
            canvas.showPage()
            y = alto - 100

    # Línea final y totales
    y -= 5
    canvas.setStrokeColor(colors.darkgrey)
    canvas.line(50, y, 550, y)
    y -= 15
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.darkblue)
    canvas.drawString(60, y, "Totales:")
    canvas.drawRightString(260, y, str(total_cant))
    canvas.drawRightString(330, y, f"${total_venta:.2f}")
    canvas.drawRightString(400, y, f"${total_ganancia:.2f}")
