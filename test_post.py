import httpx
import asyncio

async def test():
    # Login as conductor
    async with httpx.AsyncClient() as client:
        res = await client.post("http://127.0.0.1:8000/auth/login", data={"username": "conductor@resqauto.com", "password": "123"})
        if res.status_code != 200:
            res = await client.post("http://127.0.0.1:8000/auth/login", data={"username": "conductor@resqauto.com", "password": "123"})
        token = res.json().get("access_token")
        
        headers = {"Authorization": f"Bearer {token}"}
        # Get a vehiculo correctly (conductor might not have one, so we fetch it from DB directly if needed)
        # Actually let's just make a raw post
        # Get conductor token
        res_auth = await client.post("http://127.0.0.1:8000/auth/login", data={"username": "conductor@resqauto.com", "password": "123"})
        token = res_auth.json().get("access_token")
        
        headers = {"Authorization": f"Bearer {token}"}
        # Post incidente (use a dummy UUID for vehiculo)
        files = [
            ("archivos", ("test.jpg", b"fake image content", "image/jpeg"))
        ]
        data = {
            "vehiculo_id": "00000000-0000-0000-0000-000000000000",
            "tipo_problema": "Prueba Error",
            "latitud": -17.78,
            "longitud": -63.18
        }
        res = await client.post("http://127.0.0.1:8000/incidentes/", headers=headers, data=data, files=files)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")

if __name__ == "__main__":
    asyncio.run(test())
