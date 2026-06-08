from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.websockets import manager
from app.models import HistorialRutaTecnico, Tecnico, Incidente
import uuid
import logging
from datetime import datetime
import json

router = APIRouter(prefix="/tracking", tags=["Tracking en Vivo"])
logger = logging.getLogger(__name__)

@router.websocket("/ws/{tipo}/{incidente_id}/{usuario_id}")
async def websocket_tracking(
    websocket: WebSocket,
    tipo: str,
    incidente_id: uuid.UUID,
    usuario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    await manager.connect(websocket, str(incidente_id))
    try:
        while True:
            data = await websocket.receive_text()
            # Se espera que el técnico envíe datos de ubicación: {"lat": -17.78, "lng": -63.18}
            # El conductor solo escucha (o puede enviar mensajes de control en el futuro)
            try:
                payload = json.loads(data)
                
                # Guardar en base de datos si tiene latitud/longitud
                if "latitud" in payload and "longitud" in payload:
                    # Validar si el usuario_id es el técnico asignado
                    tecnico_res = await db.execute(select(Tecnico).filter(Tecnico.usuario_id == usuario_id))
                    tecnico = tecnico_res.scalars().first()
                    
                    if tecnico:
                        incidente_res = await db.execute(select(Incidente).filter(Incidente.id == incidente_id))
                        incidente = incidente_res.scalars().first()
                        
                        if incidente and incidente.tecnico_id == tecnico.id:
                            # Almacenar el registro histórico
                            nuevo_registro = HistorialRutaTecnico(
                                id=uuid.uuid4(),
                                latitud=payload["latitud"],
                                longitud=payload["longitud"],
                                registrado_en=datetime.utcnow(),
                                incidente_id=incidente_id,
                                tecnico_id=tecnico.id,
                                tenant_id=incidente.tenant_id
                            )
                            db.add(nuevo_registro)
                            await db.commit()
                            
                            # Transmitir a todos los clientes (Conductor)
                            await manager.broadcast(
                                {
                                    "tipo": "ubicacion",
                                    "latitud": payload["latitud"],
                                    "longitud": payload["longitud"],
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "tecnico_id": str(tecnico.id)
                                },
                                str(incidente_id)
                            )
                
            except json.JSONDecodeError:
                logger.error(f"Mensaje no es JSON válido: {data}")
            except Exception as e:
                logger.error(f"Error procesando mensaje WS: {str(e)}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, str(incidente_id))
        await manager.broadcast(
            {"tipo": "desconexion", "mensaje": "Usuario desconectado", "usuario_id": str(usuario_id)},
            str(incidente_id)
        )
