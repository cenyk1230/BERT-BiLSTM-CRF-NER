import time
from bert_base.client import BertClient

with BertClient(show_server_config=False, check_version=False, check_length=False, mode='NER') as bc:
    start_t = time.perf_counter()
    str1 = '我有鸡蛋和黄瓜可以做什么？'
    str2 = '不辣的川菜。'
    rst = bc.encode([str1, str2])
    print('rst:', rst)
    print(time.perf_counter() - start_t)
