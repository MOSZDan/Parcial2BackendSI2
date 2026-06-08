import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
import random
import uuid
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_flujo_completo_ciclo3(monkeypatch):
    mock_groq = MagicMock()
    mock_groq.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"proveedor": "Groq LLaMA3", "resultado_analisis": "Motor fundido", "probabilidad_falla": 95, "recomendacion": "Cambiar motor"}'))]
    )
    
    async def mock_upload(*args, **kwargs):
        return "https://mocked-url.com/imagen_o_pdf_prueba.pdf"
    
    monkeypatch.setattr("app.api.routers.incidentes.upload_file_to_s3", mock_upload)
    monkeypatch.setattr("app.crud.crud_finanzas.upload_file_to_s3", mock_upload)
    monkeypatch.setattr("app.api.routers.finanzas.generar_pdf", MagicMock(return_value="dummy.pdf"))
    monkeypatch.setattr("os.remove", MagicMock(return_value=None))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Usamos UUID corto para evitar colision de NITs o correos
        unico = str(uuid.uuid4())[:8]
        
        # 1. Registrar Conductor
        conductor_email = f"conductor_{unico}@test.com"
        res_cond = await client.post("/auth/register", json={
            "correo": conductor_email,
            "contrasena": "secreta123",
            "nombre_completo": "Conductor C3",
            "telefono": "77777777",
            "tipo_usuario": "Conductor",
            "licencia": f"LIC-{unico}"
        })
        assert res_cond.status_code == 200, res_cond.text
        
        # 2. Login Conductor
        res_login_cond = await client.post("/auth/login", data={"username": conductor_email, "password": "secreta123"})
        token_cond = res_login_cond.json()["access_token"]
        headers_cond = {"Authorization": f"Bearer {token_cond}"}
        
        # 3. Registrar Vehículo
        res_veh = await client.post("/vehiculos/", json={
            "placa": f"{unico[:4]}AB",
            "marca": "Nissan",
            "modelo": "Hilux",
            "ano": 2021,
            "color": "Negro"
        }, headers=headers_cond)
        vehiculo_id = res_veh.json()["id"]

        # 4. Registrar Admin Taller
        admin_email = f"admin_{unico}@taller.com"
        res_admin = await client.post("/auth/register", json={
            "correo": admin_email,
            "contrasena": "secreta123",
            "nombre_completo": "Admin C3",
            "telefono": "88888888",
            "tipo_usuario": "Administrador",
            "nombre_taller": f"Taller {unico}",
            "nit_taller": f"NIT-{unico}"
        })
        
        # 5. Login Admin
        res_login_adm = await client.post("/auth/login", data={"username": admin_email, "password": "secreta123"})
        token_adm = res_login_adm.json()["access_token"]
        headers_adm = {"Authorization": f"Bearer {token_adm}"}

        # 6. Registrar Tecnico
        tec_email = f"mecanico_{unico}@test.com"
        res_tec = await client.post("/talleres/tecnicos", json={
            "nombre_completo": "Mecanico Pedro",
            "telefono": "99999999",
            "correo": tec_email
        }, headers=headers_adm)
        tecnico_id = res_tec.json()["id"]

        # 7. Login Tecnico
        res_login_tec = await client.post("/auth/login", data={"username": tec_email, "password": "temporal123"})
        token_tec = res_login_tec.json()["access_token"]
        headers_tec = {"Authorization": f"Bearer {token_tec}"}

        # 8. Solicitar Auxilio
        data = {
            "vehiculo_id": vehiculo_id,
            "tipo_problema": "Problemas de motor",
            "latitud": "-17.78",
            "longitud": "-63.18",
            "prioridad": "Alta"
        }
        files = {'archivos': ('foto.jpg', b'dummy content', 'image/jpeg')}
        res_inc = await client.post("/incidentes/", data=data, files=files, headers=headers_cond)
        incidente_id = res_inc.json()["id"]

        # --- INCIO PRUEBAS CICLO 3 ---

        # Prueba IA (CU-20)
        res_ia = await client.post("/ia/analizar", json={
            "incidente_id": incidente_id,
            "texto_audio": "El auto hace un ruido raro y echa humo blanco",
            "url_imagen": "https://storage.dummy/foto.jpg"
        }, headers=headers_adm)
        assert res_ia.status_code == 200, res_ia.text
        print("\n-> Prueba IA Disparada Exitosamente")

        # 9. Aceptar Alerta (Admin)
        await client.post("/logistica/alerta/aceptar", json={
            "incidente_id": incidente_id,
            "tecnico_id": tecnico_id
        }, headers=headers_adm)

        # 10. Actualizar Estado (Técnico) a Finalizado
        res_estado = await client.patch("/logistica/estado", json={
            "incidente_id": incidente_id,
            "nuevo_estado": "Finalizado"
        }, headers=headers_tec)
        assert res_estado.status_code == 200, res_estado.text

        # Prueba PAGOS Y PDF (CU-22, CU-23, CU-24)
        res_pago = await client.post("/finanzas/pagar", json={
            "incidente_id": incidente_id,
            "monto_total": 200.0,
            "metodo_pago": "Tarjeta",
            "token_pago": "tok_visa"
        }, headers=headers_cond)
        assert res_pago.status_code == 200, res_pago.text
        
        datos_pago = res_pago.json()
        assert datos_pago["comision_plataforma"] == 20.0 # 10%
        assert datos_pago["monto_taller"] == 180.0
        assert "url_pdf" in datos_pago
        print("-> Prueba Pagos y PDF Completada Exitosamente")

        # Prueba ANALÍTICA (CU-25, CU-26)
        res_hist = await client.get(f"/analitica/vehiculo/{vehiculo_id}/historial", headers=headers_cond)
        assert res_hist.status_code == 200
        assert len(res_hist.json()) >= 1
        print("-> Prueba Historial Vehículo Completada Exitosamente")

        res_dash = await client.get("/analitica/taller/dashboard", headers=headers_adm)
        assert res_dash.status_code == 200
        dash_data = res_dash.json()
        assert dash_data["servicios_finalizados"] >= 1
        assert dash_data["ingresos_generados"] >= 200.0
        print("-> Prueba Dashboard Analítico Taller Completada Exitosamente")
        
        print("\n¡TODAS LAS PRUEBAS DEL CICLO 3 PASARON EN VERDE!\n")
