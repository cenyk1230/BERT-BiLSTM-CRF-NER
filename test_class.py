import numpy as np
import time
from bert_base.client import BertClient
from sklearn.metrics import precision_score, recall_score, f1_score

label_map = {'chat': 0, 'dish': 1, 'make': 2, 'ingredient': 3, 'taste': 4, 'series': 5}

def get_intention(content):
    if '制作' in content or '做法' in content or '怎么做' in content:
        return 'make'
    elif '口味' in content:
        return 'taste'
    elif '原料' in content or '材料' in content or '食材' in content:
        return 'ingredient'
    elif '类型' in content or '菜系' in content or '菜谱' in content:
        return 'series'
    elif '推荐' in content or '菜品' in content or '食物' in content or '美食' in content:
        return 'dish'
    return 'chat'

X = []
y = []
with open('test_class.txt', 'r') as f:
    for line in f:
        its = line.strip().split()
        X.append(its[1])
        y.append(its[0])

y_label = [label_map[x] for x in y]

with BertClient(show_server_config=False, check_version=False, check_length=False, mode='CLASS') as bc:
    start_t = time.perf_counter()
    # str1 = '我有鸡蛋和黄瓜可以做什么？'
    # str2 = '不辣的川菜。'
    # str3 = '很辣的川菜。'
    # rst = bc.encode([str1, str2, str3])
    rst = bc.encode(X)[0]['pred_label']
    print(rst)
    print(y)
    print(np.array(rst) == np.array(y))
    rst_label = [label_map[x] for x in rst]
    print('%.4f' % precision_score(y_label, rst_label, average='macro'))
    print('%.4f' % recall_score(y_label, rst_label, average='macro'))
    print('%.4f' % f1_score(y_label, rst_label, average='macro'))

y_pred = []
for (sentence, label) in zip(X, y):
    y_pred.append(get_intention(sentence))
y_pred = [label_map[x] for x in y_pred]
print('%.4f' % precision_score(y_label, y_pred, average='macro'))
print('%.4f' % recall_score(y_label, y_pred, average='macro'))
print('%.4f' % f1_score(y_label, y_pred, average='macro'))