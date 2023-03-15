import requests
from .base import Querier, RequestAdd, RequestDelete, RequestUpdate

def check_user_exists(user_id:str):

    user_querier = Querier("user")

    user_querier = user_querier.filter_by("id", "eq", user_id)

    result = user_querier.query()

    return len(result) == 1


