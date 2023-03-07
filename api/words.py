# api to db

from .base import Querier, RequestAdd, RequestDelete, RequestUpdate
words_querier = Querier("words")
all_words = words_querier.query()






words_adder = RequestAdd("words")
# words_adder(content="test", user_id=123, server_id=456, created_at=1234567890)

words_deleter = RequestDelete("words")
words_deleter(item_id = 1) # delete by item_id

words_updater = RequestUpdate("words")
words_updater(item_id = 10, server_id="ouchcchchchchc")

# https://github.com/yiting-tom/TSMC-careerhack-2023-3rd-place-solution/blob/main/adapters/share.py


def get_all_words():
    words_querier = Querier("words")
    all_words = words_querier.query()
    filtered_words = []
    for word in all_words:
        if word['content'] != "":
            del word['server_id']
            filtered_words.append(word)
    return filtered_words

def add_one_word(content, user_id, style, server_id, created_at):
    words_adder = RequestAdd("words")
    words_adder(content=content,
                user_id=user_id,
                style = style,
                server_id=server_id,
                created_at=created_at)

# def del_one_share()