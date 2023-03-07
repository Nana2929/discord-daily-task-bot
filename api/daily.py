# %%
import requests

API = "http://140.116.245.105:9453/items/"

def add_task(user_id, server_id, name, description):
    data = {
        "created_by": user_id,
        "name": name,
        "description": description,
        "server_id": server_id,
    }

    response = requests.post(API + "task", json=data)

    return response.ok
