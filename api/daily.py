# %%
try:
    from base import Querier, RequestAdd, RequestDelete, RequestUpdate
except:
    from .base import Querier, RequestAdd, RequestDelete, RequestUpdate

from datetime import datetime

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


def get_history(filter_rules: dict):
    history_querier = Querier("history")

    for field, values in filter_rules.items():
        history_querier = history_querier.filter_by(field, "eq", values)

    return history_querier.query()


def add_history(user_id, task_id, server_id):
    data = {
        "user_id": str(user_id),
        "task_id": int(task_id),
        "server_id": str(server_id),
        "accumulate": 1,
        "consecutive": 1,
        "last_check": datetime.now().strftime("%Y-%m-%d"),
    }

    history_adder = RequestAdd("history")

    return history_adder(**data)
