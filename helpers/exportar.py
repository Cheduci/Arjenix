from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import tempfile
import barcode
from barcode.writer import ImageWriter
import webbrowser

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