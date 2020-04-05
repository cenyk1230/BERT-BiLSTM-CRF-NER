import time
from bert_base.client import BertClient

with BertClient(show_server_config=False, check_version=False, check_length=False, mode='NER') as bc:
    start_t = time.perf_counter()
    str1 = '我有鸡蛋和黄瓜可以做什么？'
    str2 = '不辣的川菜。'
    str3 = '推荐一个有香菇的菜'
    strs = [str1, str2, str3]
    rst = bc.encode(strs)
    print('rst:', rst)
    for st, sen in zip(strs, rst):
        tmp = []
        flag = False
        for i in range(len(sen)):
            if sen[i] == 'B-ING':
                tmp.append(st[i])
                flag = True
            elif sen[i] == 'I-ING':
                if flag:
                    tmp[-1] = tmp[-1] + st[i]
                else:
                    tmp.append(st[i])
                    flag = True
            else:
                flag = False
        print(tmp)

    print(time.perf_counter() - start_t)
