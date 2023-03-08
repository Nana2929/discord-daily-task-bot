# %%
try:
    from base import Querier, RequestAdd, RequestDelete, RequestUpdate
except:
    from .base import Querier, RequestAdd, RequestDelete, RequestUpdate


def add_task(user_id, server_id, name, description):
    data = {
        "created_by": str(user_id),
        "name": str(name),
        "description": str(description),
        "server_id": str(server_id),
    }

    task_adder = RequestAdd("task")

    return task_adder(**data).ok
