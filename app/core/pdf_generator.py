import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import uuid

def generar_recibo_pdf(monto: float, metodo: str, taller: str, conductor: str, numero_recibo: str) -> str:
    filename = f"{numero_recibo}.pdf"
    filepath = os.path.join(os.getcwd(), filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, 750, "RESQ AUTO - Comprobante de Servicio")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Recibo Nro: {numero_recibo}")
    c.drawString(100, 680, f"Conductor: {conductor}")
    c.drawString(100, 660, f"Taller Asignado: {taller}")
    c.drawString(100, 640, f"Método de Pago: {metodo}")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 590, f"TOTAL PAGADO: Bs. {monto}")
    
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(100, 500, "Gracias por confiar su seguridad en la red ResQ Auto.")
    
    c.save()
    return filepath
