from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Incidente, Vehiculo, Transaccion
import uuid

async def obtener_historial_vehiculo(db: AsyncSession, vehiculo_id: uuid.UUID):
    stmt = select(Incidente).filter(Incidente.vehiculo_id == vehiculo_id).order_by(Incidente.solicitado_en.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

async def obtener_dashboard_taller(db: AsyncSession, taller_id: uuid.UUID):
    # Incidentes finalizados
    stmt_completados = select(func.count(Incidente.id)).filter(Incidente.taller_id == taller_id, Incidente.estado_actual.in_(["Finalizado", "Pagado_Cerrado"]))
    res_comp = await db.execute(stmt_completados)
    total_completados = res_comp.scalar()

    # Ingresos Totales Generados
    stmt_ingresos = select(func.sum(Transaccion.monto_total)).join(Incidente, Transaccion.incidente_id == Incidente.id).filter(Incidente.taller_id == taller_id)
    res_ingresos = await db.execute(stmt_ingresos)
    ingreso_bruto = res_ingresos.scalar() or 0.0

    return {
        "servicios_finalizados": total_completados,
        "ingresos_generados": float(ingreso_bruto),
        "tasa_exito": 100.0 if total_completados > 0 else 0.0
    }
