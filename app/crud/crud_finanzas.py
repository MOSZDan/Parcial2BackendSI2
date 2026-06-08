from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Incidente, Transaccion, Comision, Comprobante, Taller, Conductor
from datetime import datetime
import uuid
from app.core.pdf_generator import generar_recibo_pdf
from app.core.storage import upload_file_to_s3
from fastapi import UploadFile
import os
import aiofiles

async def procesar_pago_y_comision(db: AsyncSession, incidente_id: uuid.UUID, monto_total: float, metodo_pago: str, token_pago: str):
    inc_res = await db.execute(select(Incidente).filter(Incidente.id == incidente_id))
    incidente = inc_res.scalars().first()
    if not incidente or incidente.estado_actual != "Finalizado":
        return None

    # Simular llamada a Stripe
    # stripe.Charge.create(amount=int(monto_total*100), currency="bob", source=token_pago)

    # 1. Transaccion
    transaccion_id = uuid.uuid4()
    db_transaccion = Transaccion(
        id=transaccion_id,
        referencia=f"TX-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        metodo_pago=metodo_pago,
        estado="Pagado",
        moneda="BOB",
        monto_total=monto_total,
        pagado_en=datetime.utcnow(),
        incidente_id=incidente.id,
        tenant_id=incidente.tenant_id,
        proveedor_pasarela="Stripe",
        token_pago_externo=token_pago
    )
    db.add(db_transaccion)

    # 2. Comision (Simularemos retención del 10% por defecto)
    porcentaje = 10.00
    monto_comision = (monto_total * porcentaje) / 100
    monto_taller = monto_total - monto_comision

    db_comision = Comision(
        id=uuid.uuid4(),
        porcentaje=porcentaje,
        monto_comision=monto_comision,
        monto_neto_taller=monto_taller,
        liquidada=False,
        calculada_en=datetime.utcnow(),
        transaccion_id=transaccion_id,
        tenant_id=incidente.tenant_id
    )
    db.add(db_comision)

    # 3. Comprobante PDF (CU-24)
    # Obtener nombres para el PDF
    t_res = await db.execute(select(Taller).filter(Taller.id == incidente.taller_id))
    taller = t_res.scalars().first()
    c_res = await db.execute(select(Conductor).filter(Conductor.id == incidente.conductor_id))
    conductor = c_res.scalars().first()
    
    nro_recibo = f"FAC-{str(transaccion_id)[:8].upper()}"
    pdf_path = generar_recibo_pdf(monto_total, metodo_pago, taller.nombre_comercial, conductor.nombre_completo, nro_recibo)
    
    # Subir PDF a Supabase S3 simulando UploadFile de FastAPI
    with open(pdf_path, "rb") as f:
        # Esto es un truco rápido para usar la misma función de storage.py
        class DummyFile:
            def __init__(self, filename, content_type, f):
                self.filename = filename
                self.content_type = content_type
                self.file = f
        dummy = DummyFile(f"{nro_recibo}.pdf", "application/pdf", f)
        url_pdf = await upload_file_to_s3(dummy, folder="recibos")
        
    os.remove(pdf_path) # Limpiar local

    db_comprobante = Comprobante(
        id=uuid.uuid4(),
        numero=nro_recibo,
        url_pdf=url_pdf,
        emitido_en=datetime.utcnow(),
        transaccion_id=transaccion_id,
        tenant_id=incidente.tenant_id
    )
    db.add(db_comprobante)
    
    incidente.estado_actual = "Pagado_Cerrado"
    
    await db.commit()
    
    return nro_recibo, url_pdf, monto_taller, monto_comision
