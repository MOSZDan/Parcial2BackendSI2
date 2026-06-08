import requests
import uuid
from requests_toolbelt.multipart.encoder import MultipartEncoder

# We need a valid token. We will just use the hardcoded admin or conductor credentials
login_data = {
    "username": "conductor@resq.com",
    "password": "123"
}
login_res = requests.post("http://127.0.0.1:8000/auth/login", data=login_data)
token = login_res.json()["access_token"]

# Let's get the vehiculo ID for this conductor
headers = {"Authorization": f"Bearer {token}"}
veh_res = requests.get("http://127.0.0.1:8000/users/me/vehiculos", headers=headers)
# if there is no vehiculos endpoint, let's just use raw SQL to find the vehiculo ID
