from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

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
