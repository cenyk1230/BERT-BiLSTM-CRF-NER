import copy

import numpy as np

from db_query import neo4j


def list2sentence(arr):
    if len(arr) == 1:
        return arr[0]
    else:
        string = ''
        for i in range(len(arr) - 2):
            string += arr[i] + '、'
        string += arr[len(arr) - 2] + '和'
        string += arr[len(arr) - 1]
        return string


class DialogManager:
    def __init__(self, local=False):
        self.state = 'S0'  # current state, 0 ~ 8
        self.intention = 'UNK'  # {UNK, dish, ingredient, taste, make}
        self.dish = 'UNK'
        self.ingredient = 'UNK'
        self.taste = 'UNK'
        self.series = 'UNK'
        self.what_confirmed = []
        self.cache = None
        self.db = neo4j(local=local)
        self.failure_times = 0  # when system fails in 3 times, return to S0

    def foodEntity2sentence(self, arr, threshold=8, cache=False):
        if len(arr) == 1:
            if cache:
                self.cache = [arr[0]['name']]
            return arr[0]['name']
        else:
            indexes = np.array(range(len(arr)))
            np.random.shuffle(indexes)

            display_num = min(threshold, len(arr))
            if cache:
                self.cache = [arr[indexes[i]]['name'] for i in range(display_num)]
            string = ''
            for i in range(display_num - 2):
                string += arr[indexes[i]]['name'] + '、'
            string += arr[indexes[display_num - 2]]['name'] + '和'
            string += arr[indexes[display_num - 1]]['name']
            if display_num < len(arr):
                string += '等'
            else:
                string += '这几样'
            return string

    def handle_dialog_stateS0(self, adict, needed_init=True):
        if needed_init:
            if 'intention' in adict:
                self.intention = adict['intention']
            else:
                self.intention = 'UNK'

            if 'dish' in adict:
                self.dish = adict['dish']
            else:
                self.dish = 'UNK'

            if 'ingredient' in adict:
                self.ingredient = adict['ingredient']
            else:
                self.ingredient = 'UNK'

            if 'taste' in adict:
                self.taste = adict['taste']
            else:
                self.taste = 'UNK'

            if 'series' in adict:
                self.series = adict['series']
            else:
                self.series = 'UNK'

        if self.intention == 'UNK':
            if (self.ingredient != 'UNK' or self.taste != 'UNK' or self.series != 'UNK') and self.dish == 'UNK':
                self.state = 'S1'
                self.what_confirmed_now = ['intention', 'dish']
                if self.taste == 'UNK' and self.series == 'UNK':
                    output = '您是想要了解使用{}可以做哪些菜吗？'.format(list2sentence(self.ingredient))
                elif self.ingredient == 'UNK' and self.series == 'UNK':
                    output = '您是想要了解可以做哪些{}的菜吗？'.format(self.taste)
                elif self.series == 'UNK':
                    output = '您是想要了解使用{}可以做哪些{}的菜吗？'.format(list2sentence(self.ingredient), self.taste)
                elif self.taste == 'UNK' and self.ingredient == 'UNK':
                    if self.series.endswith('谱') or self.series.endswith('系'):
                        output = '您是想了解{}中有哪些菜吗？'.format(self.series)
                    else:
                        output = '您是想要了解有哪些{}吗？'.format(self.series)
                elif self.taste == 'UNK':
                    if self.series.endswith('谱') or self.series.endswith('系'):
                        output = '您是想要了解使用{}可以做{}中的哪些菜吗？'.format(list2sentence(self.ingredient), self.series)
                    else:
                        output = '您是想要了解使用{}可以做哪些{}吗？'.format(list2sentence(self.ingredient), self.series)
                elif self.ingredient == 'UNK':
                    if self.series.endswith('谱') or self.series.endswith('系'):
                        output = '您是想要了解可以做{}中的哪些{}的菜吗？'.format(self.series, self.taste)
                    else:
                        output = '您是想要了解可以做哪些{}的{}吗？'.format(self.taste, self.series)
                else:
                    if self.series.endswith('谱') or self.series.endswith('系'):
                        output = '您是想要了解使用{}可以做{}中的哪些{}的菜吗？'.format(list2sentence(self.ingredient), self.series, self.taste)
                    else:
                        output = '您是想要了解使用{}可以做哪些{}的{}吗？'.format(list2sentence(self.ingredient), self.taste, self.series)

            if self.ingredient == 'UNK' and self.taste == 'UNK' and self.series == 'UNK' and self.dish != 'UNK':
                self.state = 'S1'
                output = '您具体是想了解一些关于{}的什么信息呢？'.format(self.dish)

            if self.ingredient == 'UNK' and self.taste == 'UNK' and self.series == 'UNK' and self.dish == 'UNK':
                self.state = 'S0'
                output = '请问您想要了解些什么呢？'

            if (self.ingredient != 'UNK' or self.taste != 'UNK' or self.series != 'UNK') and self.dish != 'UNK':
                self.state = 'S1'
                output = '抱歉，我没太弄明白您想要了解些什么'

        else:
            if self.intention == 'dish':
                if self.dish == 'UNK':
                    if self.ingredient == 'UNK' and self.taste == 'UNK' and self.series == 'UNK':
                        self.state = 'S2'
                        output = '菜海茫茫，您想要我具体为您推荐哪种特点的菜呀？'

                    else:
                        is_taste_not = False
                        self.state = 'S7'
                        command_ingredient = []
                        if self.ingredient != 'UNK':
                            for item in self.ingredient:
                                command_ingredient.append(('hasIngredient', item))
                        command_pos = []
                        command_neg = []
                        if self.series != 'UNK':
                            command_pos.append(('hasSeries', self.series))
                        if self.taste != 'UNK':
                            if self.taste[0] == '不':
                                is_taste_not = True
                                command_neg.append(('hasTaste', self.taste[1:]))
                            else:
                                command_pos.append(('hasTaste', self.taste))
                        foods = self.db.query_entity('Food', command_ingredient, command_pos, command_neg)
                        if len(foods) > 0:
                            output = '这里为您推荐{}菜。'.format(self.foodEntity2sentence(foods, threshold=8, cache=True))
                        else:
                            output = '抱歉，我没有找到满足您要求的菜。'
                else:
                    if self.ingredient == 'UNK' and self.taste == 'UNK' and self.series == 'UNK':
                        self.state = 'S4'
                        output = '抱歉，能再说一下您的需求吗？我没有太理解清楚。'
                    else:
                        self.state = 'S4'
                        self.what_confirmed_now = ['intention', 'dish']
                        if self.taste == 'UNK' and self.series == 'UNK':
                            output = '您是想要了解使用{}可以做哪些菜吗？'.format(list2sentence(self.ingredient))
                        elif self.ingredient == 'UNK' and self.series == 'UNK':
                            output = '您是想要了解可以做哪些{}的菜吗？'.format(self.taste)
                        elif self.series == 'UNK':
                            output = '您是想要了解使用{}可以做哪些{}的菜吗？'.format(list2sentence(self.ingredient), self.taste)
                        elif self.taste == 'UNK' and self.ingredient == 'UNK':
                            if self.series.endswith('谱') or self.series.endswith('系'):
                                output = '您是想了解{}中有哪些菜吗？'.format(self.series)
                            else:
                                output = '您是想要了解有哪些{}吗？'.format(self.series)
                        elif self.taste == 'UNK':
                            if self.series.endswith('谱') or self.series.endswith('系'):
                                output = '您是想要了解使用{}可以做{}中的哪些菜吗？'.format(list2sentence(self.ingredient), self.series)
                            else:
                                output = '您是想要了解使用{}可以做哪些{}吗？'.format(list2sentence(self.ingredient), self.series)
                        elif self.ingredient == 'UNK':
                            if self.series.endswith('谱') or self.series.endswith('系'):
                                output = '您是想要了解可以做{}中的哪些{}的菜吗？'.format(self.series, self.taste)
                            else:
                                output = '您是想要了解可以做哪些{}的{}吗？'.format(self.taste, self.series)
                        else:
                            if self.series.endswith('谱') or self.series.endswith('系'):
                                output = '您是想要了解使用{}可以做{}中的哪些{}的菜吗？'.format(list2sentence(self.ingredient), self.series,
                                                                            self.taste)
                            else:
                                output = '您是想要了解使用{}可以做哪些{}的{}吗？'.format(list2sentence(self.ingredient), self.taste,
                                                                         self.series)

            if self.intention == 'ingredient':
                if self.dish != 'UNK':
                    if self.ingredient == 'UNK' and self.taste == 'UNK' and self.series == 'UNK':
                        self.state = 'S7'
                        ingredients = self.db.query_entity('Ingredient', [('isIngredientOf', self.dish)], [], [])
                        if len(ingredients) > 0:
                            output = '{}中包含{}食材。'.format(self.dish,
                                                         self.foodEntity2sentence(ingredients, threshold=10000))
                        else:
                            output = '抱歉，我没有找到{}所包含的食材。'.format(self.dish)
                    else:
                        self.state = 'S4'
                        self.what_confirmed_now = ['intention', 'ingredient']
                        output = '您是想要了解{}中包含哪些食材吗？'.format(self.dish)
                else:
                    if self.ingredient == 'UNK' and self.taste == 'UNK' and self.series == 'UNK':
                        self.state = 'S2'
                        output = '请问您是想要了解哪种菜所需的食材呢？'
                    else:
                        self.state = 'S4'
                        output = '抱歉，能再说一下您的需求吗？我没有太理解清楚。'

            if self.intention == 'taste':
                if self.dish != 'UNK':
                    if self.ingredient == 'UNK' and self.taste == 'UNK' and self.series == 'UNK':
                        self.state = 'S7'
                        taste = self.db.query_attribute('Food', self.dish, ['hasTaste'])
                        if len(taste) > 0:
                            output = '{}是一种{}的菜。'.format(self.dish, taste[0]['hasTaste'])
                        else:
                            output = '抱歉，我没有找到{}的口味。'.format(self.dish)
                    else:
                        self.state = 'S4'
                        self.what_confirmed_now = ['intention', 'taste']
                        output = '您是想要了解{}的口味吗？'.format(self.dish)
                else:
                    if self.ingredient == 'UNK' and self.taste == 'UNK' and self.series == 'UNK':
                        self.state = 'S2'
                        output = '请问您是想要了解哪种菜的口味呢？'
                    else:
                        self.state = 'S4'
                        output = '抱歉，能再说一下您的需求吗？我没有太理解清楚。'

            if self.intention == 'make':
                if self.dish != 'UNK':
                    if self.ingredient == 'UNK' and self.taste == 'UNK' and self.series == 'UNK':
                        self.state = 'S7'
                        stepText = self.db.query_attribute('Food', self.dish, ['hasStepsText'])
                        if len(stepText) > 0:
                            output = '{}的具体做法如下：{}。'.format(self.dish, stepText[0]['hasStepsText'])
                        else:
                            output = '抱歉，我没有找到{}的具体做法。'.format(self.dish)
                    else:
                        self.state = 'S4'
                        self.what_confirmed_now = ['intention', 'make']
                        output = '您是想要了解{}的具体做法吗？'.format(self.dish)
                else:
                    if self.ingredient == 'UNK' and self.taste == 'UNK' and self.series == 'UNK':
                        self.state = 'S2'
                        output = '请问您是想要了解哪种菜的具体做法呢？'
                    else:
                        self.state = 'S4'
                        output = '抱歉，能再说一下您的需求吗？我没有太理解清楚。'

            if self.intention == 'series':
                if self.dish != 'UNK':
                    if self.ingredient == 'UNK' and self.taste == 'UNK' and self.series == 'UNK':
                        self.state = 'S7'
                        series = self.db.query_attribute('Food', self.dish, ['hasSeries'])
                        if len(series) > 0 and series[0]['hasSeries'] is not None:
                            if self.series.endswith('谱') or self.series.endswith('系'):
                                output = '{}是一种{}中的菜。'.format(self.dish, series[0]['hasSeries'])
                            else:
                                output = '{}是一种{}。'.format(self.dish, series[0]['hasSeries'])
                        else:
                            output = '抱歉，我没有找到{}所属的类型。'.format(self.dish)
                    else:
                        self.state = 'S4'
                        self.what_confirmed_now = ['intention', 'series']
                        output = '您是想要了解{}是哪种类型的菜吗？'.format(self.dish)
                else:
                    if self.ingredient == 'UNK' and self.taste == 'UNK' and self.series == 'UNK':
                        self.state = 'S2'
                        output = '请问您是想要了解哪种菜所属的类型呢？'
                    else:
                        self.state = 'S4'
                        output = '抱歉，能再说一下您的需求吗？我没有太理解清楚。'

        return output

    def handle_dialog(self, adict):
        self.what_confirmed_now = []
        if self.state == 'S0':
            output = self.handle_dialog_stateS0(adict, needed_init=True)

        elif self.state == 'S7':
            if 'intention' in adict:
                output = self.handle_dialog_stateS0(adict, needed_init=True)
            else:
                if 'dish' in adict:
                    self.dish = adict['dish']

                if 'ingredient' in adict:
                    self.ingredient = adict['ingredient']

                if 'taste' in adict:
                    self.taste = adict['taste']

                if 'series' in adict:
                    self.series = adict['series']

                if self.intention == 'dish':
                    if self.ingredient == 'UNK' and self.taste == 'UNK' and self.series == 'UNK':
                        self.state = 'S0'
                        output = '抱歉，能再说一下您的需求吗？我没有太理解清楚。'
                    else:
                        self.state = 'S1'
                        self.what_confirmed_now = ['intention', 'dish']
                        if self.taste == 'UNK' and self.series == 'UNK':
                            output = '您是想要了解使用{}可以做哪些菜吗？'.format(list2sentence(self.ingredient))
                        elif self.ingredient == 'UNK' and self.series == 'UNK':
                            output = '您是想要了解可以做哪些{}的菜吗？'.format(self.taste)
                        elif self.series == 'UNK':
                            output = '您是想要了解使用{}可以做哪些{}的菜吗？'.format(list2sentence(self.ingredient), self.taste)
                        elif self.taste == 'UNK' and self.ingredient == 'UNK':
                            if self.series.endswith('谱') or self.series.endswith('系'):
                                output = '您是想了解{}中有哪些菜吗？'.format(self.series)
                            else:
                                output = '您是想要了解有哪些{}吗？'.format(self.series)
                        elif self.taste == 'UNK':
                            if self.series.endswith('谱') or self.series.endswith('系'):
                                output = '您是想要了解使用{}可以做{}中的哪些菜吗？'.format(list2sentence(self.ingredient), self.series)
                            else:
                                output = '您是想要了解使用{}可以做哪些{}吗？'.format(list2sentence(self.ingredient), self.series)
                        elif self.ingredient == 'UNK':
                            if self.series.endswith('谱') or self.series.endswith('系'):
                                output = '您是想要了解可以做{}中的哪些{}的菜吗？'.format(self.series, self.taste)
                            else:
                                output = '您是想要了解可以做哪些{}的{}吗？'.format(self.taste, self.series)
                        else:
                            if self.series.endswith('谱') or self.series.endswith('系'):
                                output = '您是想要了解使用{}可以做{}中的哪些{}的菜吗？'.format(list2sentence(self.ingredient), self.series,
                                                                            self.taste)
                            else:
                                output = '您是想要了解使用{}可以做哪些{}的{}吗？'.format(list2sentence(self.ingredient), self.taste,
                                                                         self.series)
                elif self.intention == 'ingredient':
                    if self.dish == 'UNK':
                        self.state = 'S0'
                        output = '抱歉，能再说一下您的需求吗？我没有太理解清楚。'
                    else:
                        self.state = 'S1'
                        self.what_confirmed_now = ['intention', 'ingredient']
                        output = '您是想要了解{}包含哪些食材吗？'.format(self.dish)
                elif self.intention == 'taste':
                    if self.dish == 'UNK':
                        self.state = 'S0'
                        output = '抱歉，能再说一下您的需求吗？我没有太理解清楚。'
                    else:
                        self.state = 'S1'
                        self.what_confirmed_now = ['intention', 'taste']
                        output = '您是想要了解{}是哪种口味的菜吗？'.format(self.dish)
                elif self.intention == 'make':
                    if self.dish == 'UNK':
                        self.state = 'S0'
                        output = '抱歉，能再说一下您的需求吗？我没有太理解清楚。'
                    else:
                        self.state = 'S1'
                        self.what_confirmed_now = ['intention', 'make']
                        output = '您是想要了解{}是怎么做的吗？'.format(self.dish)
                elif self.intention == 'series':
                    if self.dish == 'UNK':
                        self.state = 'S0'
                        output = '抱歉，能再说一下您的需求吗？我没有太理解清楚。'
                    else:
                        self.state = 'S1'
                        self.what_confirmed_now = ['intention', 'series']
                        output = '您是想要了解{}是哪种类型的菜吗？'.format(self.dish)
                else:
                    self.state = 'S0'
                    output = '抱歉，能再说一下您的需求吗？我没有太理解清楚。'

        elif self.state == 'S1':
            if len(self.what_confirmed) > 0 and 'confirm' in adict:
                if adict['confirm']:
                    self.intention = self.what_confirmed[1]

                    if self.intention == 'dish':
                        self.dish = 'UNK'
                    elif self.intention in ['ingredient', 'taste', 'make', 'series']:
                        self.ingredient = 'UNK'
                        self.taste = 'UNK'
                        self.series = 'UNK'

                    output = self.handle_dialog_stateS0(adict, needed_init=False)
                else:
                    output = self.handle_dialog_stateS0(adict, needed_init=True)
            elif 'intention' in adict:
                self.intention = adict['intention']
                if 'dish' in adict:
                    self.dish = adict['dish']

                if 'ingredient' in adict:
                    self.ingredient = adict['ingredient']

                if 'taste' in adict:
                    self.taste = adict['taste']

                if 'series' in adict:
                    self.series = adict['series']

                output = self.handle_dialog_stateS0(adict, needed_init=False)
            else:
                output = self.handle_dialog_stateS0(adict, needed_init=True)

        elif self.state == 'S2':
            if 'intention' in adict and adict['intention'] != self.intention:
                output = self.handle_dialog_stateS0(adict, needed_init=True)
            else:
                if self.intention == 'dish':
                    if 'ingredient' in adict:
                        self.ingredient = adict['ingredient']

                    if 'taste' in adict:
                        self.taste = adict['taste']

                    if 'series' in adict:
                        self.series = adict['series']

                    self.dish = 'UNK'
                    output = self.handle_dialog_stateS0(adict, needed_init=False)
                elif self.intention in ['ingredient', 'taste', 'make', 'series']:
                    if 'dish' in adict:
                        self.dish = adict['dish']

                    self.ingredient = 'UNK'
                    self.taste = 'UNK'
                    self.series = 'UNK'
                    output = self.handle_dialog_stateS0(adict, needed_init=False)
                else:
                    self.state = 'S0'
                    output = '抱歉，能再说一下您的需求吗？我没有太理解清楚。'

        elif self.state == 'S3':
            output = self.handle_dialog_stateS0(adict, needed_init=True)

        elif self.state == 'S4':
            if len(self.what_confirmed) > 0 and 'confirm' in adict:
                if adict['confirm']:
                    self.intention = self.what_confirmed[1]

                    if self.intention == 'dish':
                        self.dish = 'UNK'
                    elif self.intention in ['ingredient', 'taste', 'make', 'series']:
                        self.ingredient = 'UNK'
                        self.taste = 'UNK'
                        self.series = 'UNK'

                    output = self.handle_dialog_stateS0(adict, needed_init=False)
                else:
                    output = self.handle_dialog_stateS0(adict, needed_init=True)
            elif 'confirm' not in adict:
                output = self.handle_dialog_stateS0(adict, needed_init=True)
            else:
                output = self.handle_dialog_stateS0(adict, needed_init=True)

        elif self.state == 'S5':
            output = self.handle_dialog_stateS0(adict, needed_init=True)

        elif self.state == 'S6':
            output = self.handle_dialog_stateS0(adict, needed_init=True)

        self.what_confirmed = self.what_confirmed_now

        if self.state in ['S0', 'S7']:
            self.failure_times = 0
        else:
            self.failure_times += 1
            if self.failure_times >= 3:
                output = '抱歉，能再说一下您的需求吗？我没有太理解清楚。'
                self.what_confirmed = []

        return output


if __name__ == '__main__':
    dm = DialogManager()
    # output = dm.handle_dialog({'ingredient': ['韭菜', '鸡蛋', '盐']})
    # output = dm.handle_dialog({'intention': 'dish', 'taste': '辣'})
    # output = dm.handle_dialog({'dish': '宫保鸡丁'})
    # print(output, dm.state)
    #
    # output = dm.handle_dialog({'intention': 'make'})
    # print(output, dm.state)

    # output = dm.handle_dialog({'intention': 'dish', 'series': '川菜'})
    # print(output, dm.state)
    #
    # output = dm.handle_dialog({'intention': 'dish', 'taste': '不辣'})
    # print(output)
    #
    # output = dm.handle_dialog({'intention': 'series', 'dish': '老干妈鸡蛋炒面'})
    # print(output)
    # # output = dm.handle_dialog({'confirm': False, 'intention': 'taste', 'dish': '鱼香肉丝'})
    # # print(output)

    print('用鸡蛋可以做的菜')
    output = dm.handle_dialog({'intention': 'dish', 'ingredient': ['鸡蛋']})
    print(output)

    print('辣的呢？')
    output = dm.handle_dialog({'taste': '辣'})
    print(output)

    print('是的')
    output = dm.handle_dialog({'confirm': True})
    print(output)

    print('怎么做？')
    output = dm.handle_dialog({'intention': 'make'})
    print(output)

    print('蜀香鸡')
    output = dm.handle_dialog({'dish': '蜀香鸡'})
    print(output)

    print('那松子鱼属于哪种菜系呢？')
    output = dm.handle_dialog({'intention': 'series', 'dish': '松子鱼'})
    print(output)




