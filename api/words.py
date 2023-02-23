# api to db

from base import RequestAdd, RequestDelete, RequestUpdate
words_adder = RequestAdd("words")
# words_adder(content="test", user_id=123, server_id=456, created_at=1234567890)

words_deleter = RequestDelete("words")
words_deleter(item_id = 1) # delete by item_id

words_updater = RequestUpdate("words")
words_updater(item_id = 10, server_id="ouchcchchchchc")

# https://github.com/yiting-tom/TSMC-careerhack-2023-3rd-place-solution/blob/main/adapters/share.py