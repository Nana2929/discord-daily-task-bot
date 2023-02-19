import os
import dataclasses
import requests
from typing import Any

from utils.logger import L
from dotenv import load_dotenv

load_dotenv() # ./myenv.env
API_URL = os.getenv("DIRECTUS_API")


class Request:
    def __init__(self, resource):
        self._resource = resource
        self._url = f"{API_URL}/items/{resource}"
        self._params = {"fields[]": ""}
