#coding:utf-8

from flask import Flask, request, abort
import hashlib
import xmltodict
import time
import re
from py2neo import Graph, cypher
from bert_base.client import BertClient

from db_query import neo4j
from ac import ACMachine
from DM import DialogManager

def load_data(name):
    res = []
    with open(name, 'r') as f:
        for line in f:
            res.append(line.strip())
    return res

def build_machine():
    ings = load_data('ingredient.txt')
    dish = load_data('dish.txt')
    taste = load_data('taste.txt')
    series = load_data('series.txt')
    data = {'ings': ings, 'dish': dish, 'taste': taste, 'series': series}
    res = {'ings': ACMachine(), 'dish': ACMachine(), 'taste': ACMachine(), 'series': ACMachine()}
    for key, value in data.items():
        res[key].build_trie(value)
        res[key].build_ac()
    return res

db = neo4j(local=True)
machines = build_machine()
managers = {}
lasttime = {}
mapping = {'ings': 'hasIngredient', 'taste': 'hasTaste'}
translating = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
               '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9}

#微信的token令牌
WECHAT_TOKEN = "loveyou"

app = Flask(__name__)

def get_intention(content):
    if '制作' in content or '做法' in content or '怎么做' in content:
        return 'make'
    elif '口味' in content:
        return 'taste'
    elif '原料' in content or '材料' in content or '食材' in content:
        return 'ingredient'
    elif '类型' in content or '菜系' in content or '菜谱' in content:
        return 'series'
    elif '推荐' in content or '菜' in content or '菜品' in content or '食物' in content or '美食' in content:
        return 'dish'
    return None


def query(user, content):
    if user not in managers:
        managers[user] = DialogManager(local=True)
    elif user in lasttime and time.time() - lasttime[user] > 120:
        managers[user] = DialogManager(local=True)
    lasttime[user] = time.time()

    dic = {}
    intention = get_intention(content)
    if intention is not None:
        dic['intention'] = intention
    tokens = machines['dish'].match(content)
    if len(tokens) > 0:
        print('dish', tokens)
        dic['dish'] = tokens[0]
    else:
        nums = re.findall(r'第.个', content)
        flag = True
        if len(nums) > 0:
            dishes = managers[user].cache
            if dishes is not None and nums[0][1] in translating:
                num = translating[nums[0][1]]
                if num <= len(dishes):
                    flag = False
                    dic['dish'] = dishes[num - 1]
        if flag:
            tokens = machines['ings'].match(content)
            if len(tokens) > 0:
                print('ings', tokens)
                dic['ingredient'] = tokens
            tokens = machines['taste'].match(content)
            if len(tokens) > 0:
                print('taste', tokens)
                dic['taste'] = tokens[0]
            tokens = machines['series'].match(content)
            if len(tokens) > 0:
                print('series', tokens)
                dic['series'] = tokens[0]
        if intention is 'make' and managers[user].cache is not None and len(managers[user].cache) == 1:
            dic['dish'] = managers[user].cache[0]

    if '不是' in content:
        dic['confirm'] = False
    elif '是' in content or '嗯' in content or '恩'in content:
        dic['confirm'] = True

    print('user input:', content)
    print(dic)
    response = managers[user].handle_dialog(dic)

    if '具体做法如下' in response:
        response = response.replace('`', '')
        response = response.replace(';', '\n')
        response = response[:-2]
        response = '：\n'.join(response.split('：'))

    # query_st = {'rel': [], 'attr': []}
    # for key, machine in machines.items():
    #     tokens = machine.match(content)
    #     print(key, tokens)
    #     for token in tokens:
    #         if key == 'ings':
    #             query_st['rel'].append((mapping[key], token))
    #         elif key == 'taste':
    #             query_st['attr'].append((mapping[key], token))

    # if len(query_st) == 0:
    #     return '抱歉，没有找到你要的菜品。'
    # entity = db.query_entity('Food', query_st['rel'], query_st['attr'], [])
    # if len(entity) == 0:
    #     return '抱歉，没有找到你要的菜品。'
    # entity = [x['name'] for x in entity]
    # if len(entity) > 10:
    #     entity = entity[:10]
    # response = '为您推荐' + '，'.join(entity) + '。'
    return response

@app.route("/wechat80", methods = ["GET","POST"])
def wechat():
    """"对接微信公众号服务器"""
    #接收微信服务器发送的参数
    signature = request.args.get("signature")
    timestamp = request.args.get("timestamp")
    nonce = request.args.get("nonce")


    #校验参数
    if not all([signature,timestamp,nonce]):
        abort(400)

    #按照微信的流程进行计算签名
    li = [WECHAT_TOKEN,timestamp,nonce]
    #排序
    li.sort()
    #拼接字符串
    tmp_str = "".join(li)
    #进行sha1加密，得到正确的签名值
    sign = hashlib.sha1(tmp_str.encode("utf8")).hexdigest()

    # bc = BertClient(show_server_config=False, port=6666, port_out=6667, check_version=False, check_length=False, mode='NER')
    #将自己计算的签名值和请求的签名参数进行对比，如果相同，则证明请求来自微信服务器
    if signature != sign:
        #表示请求不是微信发的
        abort(403)
    else:
        #表示是微信发送的请求
        if request.method == "GET":
            #表示是第一次接入微信服务器的验证
            echostr = request.args.get("echostr")
            if not echostr:
                abort(400)
            return echostr
        elif request.method == "POST":
            #表示微信服务器转发消息过来
            xml_str = request.data
            if not xml_str:
                abort(400)

            #对xml字符串进行解析
            xml_dict = xmltodict.parse(xml_str)
            xml_dict = xml_dict.get("xml")
            user = xml_dict.get("FromUserName")

            #提取消息类型
            msg_type = xml_dict.get("MsgType")
            if msg_type =="text":
                #表示发送的是文本消息
                #构造返回值，经由微信服务器回复给用户的消息内容
                rst = query(user, xml_dict.get("Content"))
                resp_dict = {
                    "xml":{
                        "ToUserName": xml_dict.get("FromUserName"),
                        "FromUserName": xml_dict.get("ToUserName"),
                        "CreateTime": int(time.time()),
                        "MsgType":"text",
                        "Content": rst 
                    }
                }
            else:
                resp_dict = {
                    "xml": {
                        "ToUserName": xml_dict.get("FromUserName"),
                        "FromUserName": xml_dict.get("ToUserName"),
                        "CreateTime": int(time.time()),
                        "MsgType": "text",
                        "Content": "请输入文字消息，亲"
                    }
                }

            #将字典转换为xml字符串
            resp_xml_str = xmltodict.unparse(resp_dict)
            #返回消息数据给微信服务器
            print(resp_xml_str)
            return resp_xml_str

if __name__ == '__main__':
    app.run(host='0.0.0.0',port = 80, debug = False)
