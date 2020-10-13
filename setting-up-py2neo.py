from py2neo import Graph, NodeMatcher
from py2neo.data import Node, Relationship
from py2neo.ogm import *
import csv
from tkinter import *

MESSAGAE = '''
====================================================================================================
	CHOICE A) Given a disease id, what is its name, what are drug names that can treat or 
	palliate this disease, what are gene names that cause this disease, and where 
	this disease occurs?

	CHOICE B) We assume that a compound can treat a disease if the compound or its resembled compound 
	up-regulates/down- regulates a gene, but the location down-regulates/up-regulates the gene 
	in an opposite direction where the disease occurs. Find all compounds that can treat a new
	disease name (i.e. the missing edges between compound and disease excluding existing drugs).

	ENTER "A" for CHOICE A
	ENTER "B" for CHOICE B
====================================================================================================
'''

graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))
graph.delete_all()


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
    next(nodes_read_tsv, None) # skip first row
    for row in nodes_read_tsv:
        ID = row[0].split("::")[1]
        Name = row[1]
        kind = row[2]
        node = Node(kind, name = Name, id = ID)
        graph.create(node)
    nodes_tsv_file.close()

def readEdges():
    edges_tsv_file = open("sample_edges.tsv")
    edges_read_tsv = csv.reader(edges_tsv_file, delimiter = "\t")
    next(edges_read_tsv, None) # skip first row
    for row in edges_read_tsv:
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

# Given a disease id, 
# what is its name, 
# what are drug names that can treat or palliate this disease, 
# what are gene names that cause this disease, 
# and where this disease occurs? 
# Obtain and output this information in a single query.
def queryDisease(diseaseID):
    query = f"""
        MATCH (c:Compound)-[:treats|palliates]->(d:Disease {{id: "{diseaseID}"}})
        OPTIONAL MATCH (g:Gene)-[:associates]->(d:Disease {{id: "{diseaseID}"}})
        OPTIONAL MATCH (d:Disease {{id: "{diseaseID}"}})-[:localizes]->(a:Anatomy)
        RETURN d.name, c.name, g.name, a.name
    """
    results = graph.run(query).data()

    if not results:
        print("No record found")
        return False
    else:
        for result in results:
            print(f"\t{result['d.name']}")
            print(f"\t{result['c.name']}")
            print(f"\t{result['g.name']}")
            print(f"\t{result['a.name']}")
        return True


# We assume that a compound can treat a disease 
# if the compound or its resembled compound up-regulates/down-regulates a gene, 
# but the location down-regulates/up-regulates the gene in an opposite direction where the disease occurs. 
# Find all compounds that can treat a new disease name 
# (i.e. the missing edges between compound and disease excluding existing drugs). 
# Obtain and output all drugs in a single query.
def queryCompound(compound):
    query = f"""
        MATCH (c:Compound {{name: "{compound}"}})-[:upregulates]->(:Gene)<-[:downregulates]-(d:Disease)
        WHERE NOT (c)-[:treats]->(d)
        OPTIONAL MATCH (c:Compound {{name: "{compound}"}})-[:downregulates]->(:Gene)<-[:upregulates]-(d:Disease)
        WHERE NOT (c)-[:treats]->(d)
        RETURN DISTINCT c.name, d.name
    """

    # Optional node query
    # query = f"""
    #     MATCH (c)-[:upregulates]->(d:Gene)
    #     WHERE c:Compound OR c:Disease
    #     RETURN c.name, d.name
    # """

    # Find resemble compound
    # query = f"""
    #      MATCH (c:Compound {{name: "{compound}"}})-[:resembles]-(d:Compound)
    #      RETURN DISTINCT c.name, d.name
    # """
    results = graph.run(query).data()
    if not results:
        print("No results found")
    else:
        print("Compound-Disease pairs:")
        for result in results:
            print(f"\t{result['c.name']}-{result['d.name']}")

def main():
    readNodes()
    readEdges()

    # https://www.youtube.com/watch?v=_lSNIrR1nZU
    # window = Tk()
    # window.title("Hetio-Net by Yi Heng & Liulan ")
    # window.configure(background="black")

    # Label(window, text=MESSGAE, bg="black", fg="white", font="none 12 bold")

    # textentry - Entry(window, width=20, bg="white")
    print(MESSAGAE)

    choice = input("Please enter your choice: ")
    while(choice != "A" and choice != "B"):
        choice = input("Invalid Choice. Please re-enter << ")


    if choice == 'A':
        query = input("Please enter a disease ID: ")
        while(not queryDisease(query)):
        	query = input ("Invalid ID was entered. Please re-enter: ")

    # if choice == 'B':
    #     query = input("Please enter a compound name: ")
    #     queryCompound(query)

if __name__ == "__main__":
    main()
