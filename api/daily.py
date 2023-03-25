# %%
try:
    from base import Querier, RequestAdd, RequestDelete, RequestUpdate
except:
    from .base import Querier, RequestAdd, RequestDelete, RequestUpdate
from typing import Union, List
from datetime import datetime
import pytz


def add_task(user_id, server_id, name, description):
    data = {
        "created_by": str(user_id),
        "name": str(name),
        "description": str(description),
        "server_id": str(server_id),
    }

    task_adder = RequestAdd("task")

    return task_adder(**data).ok


def get_task(filter_rules: dict):
    task_querier = Querier("task")

    for field, values in filter_rules.items():
        task_querier = task_querier.filter_by(field, "eq", values)

    return task_querier.query()


def get_history(filter_rules: dict = {}):

    history_querier = Querier("history")

    history_querier.fields("fields",
                           "task_id.name,task_id.id,user_id.time_zone")

    for field, values in filter_rules.items():
        history_querier = history_querier.filter_by(field, "eq", values)

    return history_querier.query()


def add_history(user_id: str, task_id: int, server_id: str,
                last_check: datetime, **kwargs):
    data = {
        "user_id": str(user_id),
        "task_id": int(task_id),
        "server_id": str(server_id),
        "accumulate": 1,
        "consecutive": 1,
        "last_check": last_check.strftime("%Y-%m-%d"),
    }

    history_adder = RequestAdd("history")

    return history_adder(**data)


def update_history(id: int, accumulate: int, consecutive: int,
                   last_check: Union[datetime, str], **kwargs):

    history_updater = RequestUpdate("history")
    if isinstance(last_check, datetime):
        last_check = last_check.strftime("%Y-%m-%d")
    return history_updater(id,
                           accumulate=int(accumulate),
                           consecutive=int(consecutive),
                           last_check=last_check).ok


def delete_task_by_id(item_id):
    task_deleter = RequestDelete("task")
    task_deleter(item_id=item_id)


def delete_task_by_ids(task_ids: List[int]):
    """Batch delete tasks by task ids.
    Parameters
    ----------
    task_ids : List[int]
        a batch of task ids to be deleted from database
    """
    for item_id in task_ids:
        delete_task_by_id(item_id)
