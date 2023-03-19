# %%
try:
    from .base import Querier, RequestAdd, RequestDelete, RequestUpdate
except:
    from base import Querier, RequestAdd, RequestDelete, RequestUpdate


def add_subscribe(task_id: int, user_id: str, server_id: str, remind_time: int, condemn_time: int, channel_id: str, **kwargs):

    subscribe_adder = RequestAdd("subscribe")

    return subscribe_adder(
        task_id=int(task_id),
        user_id=str(user_id),
        server_id=str(server_id),
        remind_time=int(remind_time),
        condemn_time=int(condemn_time),
        channel_id=str(channel_id),
    ).ok


def get_subscribe(filter_rules, **kwargs):

    subscribe_querier = Querier("subscribe")

    subscribe_querier.fields(
        "fields", "task_id.name,task_id.id,task_id.description")

    for k, v in filter_rules.items():
        subscribe_querier.filter_by(k, "eq", v)

    return subscribe_querier.query()


def update_subscribe(id, remind_time, condemn_time, channel_id: str, **kwargs):

    subscribe_updater = RequestUpdate("subscribe")
    return subscribe_updater(
        item_id=id,
        remind_time=remind_time,
        condemn_time=condemn_time,
        channel_id=channel_id
    ).ok


def delete_subscribe(id: int, **kwargs):

    subscribe_deleter = RequestDelete("subscribe")
    return subscribe_deleter(item_id=int(id)).ok
