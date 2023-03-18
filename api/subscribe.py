# %%
try:
    from .base import Querier, RequestAdd, RequestDelete, RequestUpdate
except:
    from base import Querier, RequestAdd, RequestDelete, RequestUpdate

def add_subscribe(task_id:int, user_id:str, server_id:str, remind_time:int, condemn_time:int, **kwargs):

    subscribe_adder = RequestAdd("subscribe")

    return subscribe_adder(
        task_id=int(task_id),
        user_id=str(user_id),
        server_id=str(server_id),
        remind_time=int(remind_time),
        condemn_time=int(condemn_time)
    ).ok


def get_subscribe(user_id: str, server_id:str, **kwargs):

    subscribe_querier = Querier("subscribe")

    subscribe_querier.fields("fields", "task_id.name,task_id.id")
    subscribe_querier.filter_by("user_id", "eq", user_id).filter_by("server_id", "eq", server_id)

    return subscribe_querier.query()

def update_subscribe(id, remind_time, condemn_time, **kwargs):

    subscribe_updater = RequestUpdate("subscribe")
    return subscribe_updater(
        item_id=id,
        remind_time=remind_time,
        condemn_time=condemn_time
    ).ok