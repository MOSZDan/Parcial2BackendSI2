import requests

# 1. Login to get token
login_data = {"username": "conductor@resq.com", "password": "123"}
r = requests.post("http://127.0.0.1:8002/auth/login", data=login_data)
token = r.json()["access_token"]

# 2. Get mis_vehiculos
headers = {"Authorization": f"Bearer {token}"}
r_veh = requests.get("http://127.0.0.1:8002/vehiculos/mis_vehiculos", headers=headers)
vehiculos = r_veh.json()
vehiculo_id = vehiculos[0]["id"]

# 3. Post incidente
files = {
    "archivos": ("foto_evidencia.jpg", b"fake_image_data", "image/jpeg")
}
data = {
    "vehiculo_id": vehiculo_id,
    "tipo_problema": "Problema Mecánico",
    "latitud": -17.78,
    "longitud": -63.18,
    "creado_offline": False
}

r_inc = requests.post("http://127.0.0.1:8002/incidentes/", headers=headers, data=data, files=files)
print("Status Code:", r_inc.status_code)
try:
    print(r_inc.json())
except:
    pass
