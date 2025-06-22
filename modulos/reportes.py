from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime

def generar_reporte_ventas_pdf(cur):
    fecha_actual = datetime.now().date()
    ruta_pdf = f"reporte_ventas_{fecha_actual.strftime('%Y-%m-%d')}.pdf"
    
    # 1. Obtener resumen general
    cur.execute("""
        SELECT COUNT(*) AS cantidad_ventas, COALESCE(SUM(total), 0)
        FROM ventas
        WHERE DATE(fecha_hora) = CURRENT_DATE;
    """)
    cantidad_ventas, total_recaudado = cur.fetchone()

    # 2. Obtener rango horario
    cur.execute("""
        SELECT MIN(fecha_hora), MAX(fecha_hora)
        FROM ventas
        WHERE DATE(fecha_hora) = CURRENT_DATE;
    """)
    primera, ultima = cur.fetchone()
    hora_primera = primera.strftime("%H:%M") if primera else "-"
    hora_ultima = ultima.strftime("%H:%M") if ultima else "-"

    # 3. Obtener productos vendidos
    cur.execute("""
        SELECT 
            p.nombre,
            SUM(dv.cantidad) AS total_cantidad,
            SUM(dv.cantidad * dv.precio_unitario) AS subtotal,
            SUM(dv.cantidad * (dv.precio_unitario - p.precio_compra)) AS ganancia
        FROM ventas v
        JOIN detalle_ventas dv ON v.id = dv.venta_id
        JOIN productos p ON p.id = dv.producto_id
        WHERE DATE(v.fecha_hora) = CURRENT_DATE
        GROUP BY p.nombre
        ORDER BY total_cantidad DESC;
    """)
    productos = cur.fetchall()

    # 4. Crear PDF
    c = canvas.Canvas(ruta_pdf, pagesize=A4)
    ancho, alto = A4
    y = alto - 2 * cm

    # Encabezado
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, f"REPORTE DE VENTAS DEL DÍA - {fecha_actual.strftime('%d/%m/%Y')}")
    y -= 1.2 * cm

    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, y, f"Ventas totales: {cantidad_ventas}")
    y -= 0.6 * cm
    c.drawString(2 * cm, y, f"Total recaudado: ${total_recaudado:,.2f}")
    y -= 0.6 * cm
    c.drawString(2 * cm, y, f"Hora de la primera venta: {hora_primera}")
    y -= 0.6 * cm
    c.drawString(2 * cm, y, f"Hora de la última venta: {hora_ultima}")
    y -= 1.2 * cm

    # Tabla de productos
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Productos vendidos:")
    y -= 0.8 * cm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "Nombre")
    c.drawRightString(11.5 * cm, y, "Cant.")
    c.drawRightString(14.5 * cm, y, "Subtotal")
    c.drawRightString(17.5 * cm, y, "Ganancia")
    y -= 0.5 * cm

    c.setFont("Helvetica", 10)
    ganancia_total = 0

    for nombre, cant, subtotal, ganancia in productos:
        if y < 2.5 * cm:
            c.showPage()
            y = alto - 2 * cm
            c.setFont("Helvetica", 10)

        c.drawString(2 * cm, y, nombre[:38])
        c.drawRightString(11.5 * cm, y, str(cant))
        c.drawRightString(14.5 * cm, y, f"${subtotal:,.2f}")
        c.drawRightString(17.5 * cm, y, f"${ganancia:,.2f}")
        ganancia_total += ganancia
        y -= 0.4 * cm

    # Resumen de ganancia
    y -= 0.8 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, f"Ganancia neta del día: ${ganancia_total:,.2f}")

    # Pie
    y -= 1.2 * cm
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(2 * cm, y, f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    c.save()

    print(f"📄 Reporte generado: {ruta_pdf}")
