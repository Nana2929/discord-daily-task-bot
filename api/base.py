from typing import Any, List, Optional, Union
import os
import dataclasses
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


field_mapping = {
    'words': ['content', 'user_id', 'server_id', 'created_at'],
}

api_url ="http://140.116.245.105:9453/items"

class Request:
    def __init__(self, collection):
        self._collection = collection
        self._fields = field_mapping[collection].copy()
        self._url = f"{api_url}/{collection}"
    def query(self, **kwargs):
        return requests.get(self.url, params=kwargs)

    def drop_field(self, field: str):
        if field in self._fields:
            self._fields.remove(field)
        return self

    def filter_by(self, field: str, operator: str, values: str):
        key = f"filter{field}[_{operator}]"
        self._params[key] = values if not isinstance(values, list) else ",".join(values)
        return self

    def fields(self, key: str, val: str):
        self._params[key] = val
        return self

class RequestAdd(Request):
    def __init__(self, collection):
        super().__init__(collection)
    def __call__(self, **kwargs):
        return requests.post(self._url, json=kwargs)

class RequestDelete(Request):
    def __init__(self, collection):
        super().__init__(collection)
    def __call__(self, item_id: Any):
        self._url += f"/{item_id}"
        return requests.delete(self._url)


class RequestUpdate(Request):
    def __init__(self, collection):
        super().__init__(collection)
    def __call__(self, item_id: Any, **kwargs):
        self._url += f"/{item_id}"
        updated_fields_dict = {k: v for k, v in kwargs.items() if k in self._fields}
        return requests.patch(self._url, json=updated_fields_dict)