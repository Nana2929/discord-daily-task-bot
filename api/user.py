import requests
from .base import Querier, RequestAdd, RequestDelete, RequestUpdate


def check_user_exists(user_id: str):

    user_querier = Querier("user")
    user_querier = user_querier.filter_by("id", "eq", user_id)
    result = user_querier.query()
    return len(result) == 1


def add_one_user(user_id: str, time_zone: str):
    user_adder = RequestAdd("user")
    msg = user_adder(id=user_id, time_zone=time_zone)
    return msg.json()


def get_user(user_id: str):

    user_querier = Querier("user")

    user_querier = user_querier.filter_by("id", "eq", user_id)

    result = user_querier.query()

    return result[0]


def update_user(user_id: str, time_zone: str):
    user_updater = RequestUpdate("user")
    msg = user_updater(item_id=user_id, time_zone=time_zone)
    return msg.json()


def get_all_users():
    user_querier = Querier("user")
    result = user_querier.query()
    return result
