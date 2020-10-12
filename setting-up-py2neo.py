from py2neo import Graph
from py2neo.data import Node, Relationship
from py2neo.ogm import *
import csv

graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))



# https://medium.com/smith-hcv/graph-databases-neo4j-and-py2neo-for-the-absolute-beginner-8989498ebe43

# def Neo4jConnectionSetup( ):
#     uri = "bolt://localhost:7687"
#     driver = GraphDatabase.driver(uri, auth=("neo4j", "your password"))
graph.delete_all()

# initiate nodes 
Alex1 = Node ("Person", name = "Alex1")
Alex2 = Node ("Person", name = "Alex2")

# creating nodes in graph
graph.create(Alex1)
graph.create(Alex2)

# creating relationship
graph.create(Relationship(Alex1, "LOVES", Alex2))

nodes_tsv_file = open("sample_nodes.tsv")
nodes_read_tsv = csv.reader(nodes_tsv_file, delimiter = "\t")
count = 0
for row in nodes_read_tsv:
	if count == 0:
		count += 1
	else:
		ID = row[0]
		Name = row[1]
		kind = row[2]
		node = Node(kind, name = Name, id = ID)
		graph.create(node)


nodes_tsv_file.close()