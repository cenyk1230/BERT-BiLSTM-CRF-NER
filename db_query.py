from py2neo import Graph, cypher

# https://neo4j.com/developer/cypher-basics-ii/

class neo4j:
    def __init__(self, local=False):
        if local:
            self.graph = Graph("bolt://localhost:7687", password="AI2020@zxy")
        else:
            self.graph = Graph("bolt://123.57.246.134:7687", password="AI2020@zxy")

    def query_attribute(self, ntype, name, attrs):
        """
        query attribute value for a given entity
        For all attributes to query, see http://123.57.246.134:7474/
        """
        statement = """MATCH (p:{} {{name:'{}'}})
RETURN p.{} as {}""".format(ntype, cypher.cypher_escape(name), attrs[0], attrs[0])
        for attr in attrs[1:]:
            statement += ", p.{} as {}".format(attr, attr)
        return self.graph.run(statement).data()

    def query_entity(self, ntype, rel_conditions, attr_conditions, neg_attr):
        """
        query entity names for given relation and attribute conditions
        Negation conditions only support attributes for now.
        """
        statement = "MATCH (p:{})".format(ntype)
        for attr, value in attr_conditions:
            statement += "\nMATCH (p {{{}:'{}'}})".format(attr, cypher.cypher_escape(value))
        for rel, entity in rel_conditions:
            statement += "\nMATCH (p)-[:{}]->({{name:'{}'}})".format(rel, cypher.cypher_escape(entity))
        if neg_attr:
            statement += "\nWHERE p.{} <> '{}'".format(neg_attr[0][0], cypher.cypher_escape(neg_attr[0][1]))
            for attr, value in neg_attr[1:]:
                statement += "AND p.{} <> '{}'".format(attr, cypher.cypher_escape(value))
        statement += "\nRETURN p.name as name"
        return self.graph.run(statement).data()

if __name__ == '__main__':
    db = neo4j(local=False)
    # 查询宫保鸡丁的步骤和烹饪时间
    print(db.query_attribute('Food', '宫保鸡丁', ['hasStepsText', 'hasCookingTime', 'hasIngredient']))
    # 查询包括蕨菜和盐、步骤容易、不苦的菜
    print(db.query_entity('Food', [('hasIngredient', '蕨菜'), ('hasIngredient', '盐')], [('hasHardLevel', '容易')], [('hasTaste', '苦')]))
    print(db.query_entity('Food', [('hasIngredient', '蕨菜'), ('hasIngredient', '肉末')], [], []))
    print(db.query_entity('Food', [('hasIngredient', '鸡蛋'), ('hasTaste', '咸')], [], []))

    # print(db.query_entity('Ingredient', [('isIngredientOf', '宫保鸡丁')], [], []))
    # all_ings = db.query_entity('Food', [], [], [])
    # with open('all_food.txt', 'w') as f:
    #     for ing in all_ings:
    #         f.write(ing['name'] + '\n')
