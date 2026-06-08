import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
import random

@pytest.mark.asyncio
async def test_flujo_completo(monkeypatch):
    # Mockear S3 para evitar subir archivos de verdad
    async def mock_upload(*args, **kwargs):
        return "https://mocked-url.com/imagen_prueba.jpg"
    monkeypatch.setattr("app.api.routers.incidentes.upload_file_to_s3", mock_upload)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Registrar Conductor
        conductor_email = f"conductor_{random.randint(1000,9999)}@test.com"
        res_cond = await client.post("/auth/register", json={
            "correo": conductor_email,
            "contrasena": "secreta123",
            "nombre_completo": "Conductor de Prueba",
            "telefono": "77777777",
            "tipo_usuario": "Conductor",
            "licencia": f"LIC-{random.randint(100,999)}"
        })
        assert res_cond.status_code == 200, res_cond.text
        
        # 2. Iniciar sesión Conductor
        res_login_cond = await client.post("/auth/login", data={"username": conductor_email, "password": "secreta123"})
        assert res_login_cond.status_code == 200, res_login_cond.text
        token_cond = res_login_cond.json()["access_token"]
        headers_cond = {"Authorization": f"Bearer {token_cond}"}
        
        # 3. Registrar Vehículo
        res_veh = await client.post("/vehiculos/", json={
            "placa": f"{random.randint(100,999)}AB",
            "marca": "Toyota",
            "modelo": "Corolla",
            "ano": 2020,
            "color": "Rojo"
        }, headers=headers_cond)
        assert res_veh.status_code == 200, res_veh.text
        vehiculo_id = res_veh.json()["id"]

        # 4. Registrar Admin Taller
        admin_email = f"admin_{random.randint(1000,9999)}@taller.com"
        res_admin = await client.post("/auth/register", json={
            "correo": admin_email,
            "contrasena": "secreta123",
            "nombre_completo": "Admin Prueba",
            "telefono": "88888888",
            "tipo_usuario": "Administrador",
            "nombre_taller": "Taller E2E",
            "nit_taller": f"{random.randint(10000,99999)}"
        })
        assert res_admin.status_code == 200, res_admin.text
        
        # 5. Iniciar sesión Admin
        res_login_adm = await client.post("/auth/login", data={"username": admin_email, "password": "secreta123"})
        assert res_login_adm.status_code == 200, res_login_adm.text
        token_adm = res_login_adm.json()["access_token"]
        headers_adm = {"Authorization": f"Bearer {token_adm}"}

        # 6. Consultar especialidades
        res_esp = await client.get("/talleres/especialidades")
        assert res_esp.status_code == 200, res_esp.text
        especialidades = res_esp.json()
        if especialidades:
            esp_id = especialidades[0]["id"]
            res_asig = await client.post("/talleres/especialidades", json={"especialidad_ids": [esp_id]}, headers=headers_adm)
            assert res_asig.status_code == 200, res_asig.text

        # 7. Registrar Tecnico
        tec_email = f"mecanico_{random.randint(1000,9999)}@test.com"
        res_tec = await client.post("/talleres/tecnicos", json={
            "nombre_completo": "Mecanico Juan",
            "telefono": "99999999",
            "correo": tec_email
        }, headers=headers_adm)
        assert res_tec.status_code == 200, res_tec.text
        tecnico_id = res_tec.json()["id"]

        # 8. Iniciar sesión Tecnico (con pass temporal123)
        res_login_tec = await client.post("/auth/login", data={"username": tec_email, "password": "temporal123"})
        assert res_login_tec.status_code == 200, res_login_tec.text
        token_tec = res_login_tec.json()["access_token"]
        headers_tec = {"Authorization": f"Bearer {token_tec}"}

        # 9. Solicitar Auxilio (Conductor)
        data = {
            "vehiculo_id": vehiculo_id,
            "tipo_problema": "Llanta pinchada",
            "latitud": "-17.78",
            "longitud": "-63.18",
            "prioridad": "Alta"
        }
        files = {'archivos': ('foto.jpg', b'dummy content', 'image/jpeg')}
        res_inc = await client.post("/incidentes/", data=data, files=files, headers=headers_cond)
        assert res_inc.status_code == 200, res_inc.text
        incidente_id = res_inc.json()["id"]

        # 10. Aceptar Alerta (Admin)
        res_accept = await client.post("/logistica/alerta/aceptar", json={
            "incidente_id": incidente_id,
            "tecnico_id": tecnico_id
        }, headers=headers_adm)
        assert res_accept.status_code == 200, res_accept.text

        # 11. Actualizar Estado (Técnico)
        res_estado = await client.patch("/logistica/estado", json={
            "incidente_id": incidente_id,
            "nuevo_estado": "Llegada"
        }, headers=headers_tec)
        assert res_estado.status_code == 200, res_estado.text

        # 12. Cancelar Solicitud (Conductor)
        res_cancel = await client.post("/logistica/cancelar", json={
            "incidente_id": incidente_id,
            "motivo": "Resolvi el problema"
        }, headers=headers_cond)
        assert res_cancel.status_code == 200, res_cancel.text
        
        print("TODOS LOS TESTS E2E PASARON CORRECTAMENTE!")
