from py2neo import Graph, NodeMatcher
from py2neo.data import Node, Relationship
from py2neo.ogm import *
import csv

# def createGraph():
graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))
graph.delete_all()


# https://medium.com/smith-hcv/graph-databases-neo4j-and-py2neo-for-the-absolute-beginner-8989498ebe43

# def Neo4jConnectionSetup( ):
#     uri = "bolt://localhost:7687"
#     driver = GraphDatabase.driver(uri, auth=("neo4j", "your password"))


# initiate nodes 
# Alex1 = Node ("Person", name = "Alex1")
# Alex2 = Node ("Person", name = "Alex2")

# # creating nodes in graph
# graph.create(Alex1)
# graph.create(Alex2)

# # creating relationship
# graph.create(Relationship(Alex1, "LOVES", Alex2))
def getRelationship(letter):
	relationship = ""
	if letter =='b':
		relationship = "binds"
	elif letter=='c':
		relationship = "covaries"
	elif letter=='r':
		relationship = "resembles"
	elif letter=='t':
		relationship = "treats"
	elif letter=='p':
		relationship = "palliates"
	elif letter=='a':
		relationship = "associates"
	elif letter=='d':
		relationship = "downregulates"
	elif letter=='u':
		relationship = "upregulates"
	elif letter=='i':
		relationship = "interacts"
	elif letter=='e':
		relationship = "expresses"
	elif letter=='l':
		relationship = "localizes"

	return relationship

def readNodes():
	nodes_tsv_file = open("sample_nodes.tsv")
	nodes_read_tsv = csv.reader(nodes_tsv_file, delimiter = "\t")
	count = 0
	for row in nodes_read_tsv:
		if count == 0:
			count += 1
		else:
			ID = row[0].split("::")[1]
			Name = row[1]
			kind = row[2]
			node = Node(kind, name = Name, id = ID)
			graph.create(node)
	nodes_tsv_file.close()

def readEdges():
	edges_tsv_file = open("sample_edges.tsv")
	edges_read_tsv = csv.reader(edges_tsv_file, delimiter = "\t")
	count = 0
	for row in edges_read_tsv:
		if count == 0:
			count += 1
		else:
			type_ID = row[0].split("::")  # e.g ['Compound', 'DB00035']
			source_type = type_ID[0] # e.g Compound
			source_ID = type_ID[1] # DB00035

			relation = row[1] # CbG
			relationship = getRelationship(row[1][1]) # "CbG" => "binds"
			
			type_target_ID= row[2].split("::")
			target_type = type_target_ID[0]
			target_ID= type_target_ID[1]
		
			query = f"""
			MATCH (a:{source_type}),(b:{target_type})
			WHERE a.id = '{source_ID}' AND b.id = '{target_ID}'
			CREATE (a)-[r: {relationship}]->(b)
			"""
			graph.run(query)


        	

	edges_tsv_file.close()


def main():
    readNodes()
    readEdges()


    # print(MESSGAE)

    # choice = input("Please enter your choice: ")
    # while(choice != "A" and choice != "B"):
    #     choice = input("Invalid Choice. Please re-enter << ")
    


    # if choice == 'A':
    #     query = input("Please enter a disease name: ")
  

    


if __name__ == "__main__":
    main()
