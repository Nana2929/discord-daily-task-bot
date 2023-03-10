# %%
import requests
from typing import List 
from .base import (
    Querier,
    RequestAdd,
    RequestDelete,
    api_url)


def add_task(user_id, server_id, name, description):
    # 好像可以改成用 RequestAdd
    data = {
        "created_by": str(user_id),
        "name": str(name),
        "description": str(description),
        "server_id": str(server_id),
    }

    response = requests.post(api_url + "task", json=data)
    return response.ok


def get_tasks_by_user_id(user_id):
    # example: 140.116.245.105:9453/items/task?filter[created_by][_eq]=346553789228122113
    task_querier = Querier("task")
    user_task = task_querier.filter_by("created_by", "eq", user_id).query()
    return user_task

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

# %%
