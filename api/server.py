from .base import Querier, RequestAdd, RequestDelete, RequestUpdate


def add_server(server_id: str, **kwargs):
    data = {
        "id": str(server_id),
    }

    server_adder = RequestAdd("server")
    return server_adder(**data).ok

def check_server_exists(server_id:str):

    server_querier = Querier("server")
    server_querier = server_querier.filter_by("id", "eq", server_id)
    result = server_querier.query()
    return len(result) == 1