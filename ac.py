import sys
import pickle

class TreeNode:
    def __init__(self):
        self.keys = []
        self.childs = []
        self.word = None

class ACMachine:
    def __init__(self):
        self.root = TreeNode()

    def build_trie(self, str_list):
        for s in str_list:
            cur = self.root
            for c in s:
                if c in cur.keys:
                    cur = cur.childs[cur.keys.index(c)]
                else:
                    cur.keys.append(c)
                    new_node = TreeNode()
                    cur.childs.append(new_node)
                    cur = new_node
            cur.word = s

    def build_ac(self):
        l = 0
        q = [self.root]
        self.root.fail = self.root
        while l < len(q):
            cur = q[l]
            l += 1
            for i in range(len(cur.keys)):
                now = cur.childs[i]
                q.append(now)
                if cur == self.root:
                    fail_node = self.root
                else:
                    fail_node = cur.fail
                    while fail_node != self.root and cur.keys[i] not in fail_node.keys:
                        fail_node = fail_node.fail
                    if cur.keys[i] in fail_node.keys:
                        fail_node = fail_node.childs[fail_node.keys.index(cur.keys[i])]
                now.fail = fail_node
                if now.word is None and fail_node.word is not None:
                    now.word = fail_node.word


    def match(self, s):
        cur = self.root
        words = set()
        for c in s:
            if c in cur.keys:
                cur = cur.childs[cur.keys.index(c)]
            else:
                cur = cur.fail
                while cur != self.root and c not in cur.keys:
                    cur = cur.fail
                if c in cur.keys:
                    cur = cur.childs[cur.keys.index(c)]
            if cur.word is not None:
                words.add(cur.word)
        res = []
        for word in words:
            flag = True
            for another in words:
                if word != another and word in another:
                    flag = False
                    break
            if flag:
                res.append(word)
        return res


if __name__ == '__main__':
    machine = ACMachine()
    # str_list = ['蛋炒饭', '炒饭鸡蛋', '蛋炒饭鸡', '蛋炒蛋', '蛋炒蛋炒', '炒蛋炒']
    name = sys.argv[1]
    str_list = []
    with open(name, 'r') as f:
        for line in f:
            str_list.append(line.strip())
    machine.build_trie(str_list)
    machine.build_ac()
    # pickle.dump(machine, open('machine.pkl', 'wb'))

    # machine = pickle.load(open('machine.pkl', 'rb'))
    # words = machine.match('蛋炒蛋炒饭鸡蛋啊')
    words = machine.match('黄瓜和鸡蛋')
    print(words)
