from fastapi import WebSocket
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Mapea un incidente_id a una lista de WebSockets activos (ej. Conductor y Técnico)
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, incidente_id: str):
        await websocket.accept()
        if incidente_id not in self.active_connections:
            self.active_connections[incidente_id] = []
        self.active_connections[incidente_id].append(websocket)
        logger.info(f"Nuevo cliente conectado al incidente {incidente_id}")

    def disconnect(self, websocket: WebSocket, incidente_id: str):
        if incidente_id in self.active_connections:
            if websocket in self.active_connections[incidente_id]:
                self.active_connections[incidente_id].remove(websocket)
            if not self.active_connections[incidente_id]:
                del self.active_connections[incidente_id]
        logger.info(f"Cliente desconectado del incidente {incidente_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict, incidente_id: str):
        if incidente_id in self.active_connections:
            for connection in self.active_connections[incidente_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error enviando mensaje: {str(e)}")
                    # La desconexión se manejará en el bloque principal

manager = ConnectionManager()
