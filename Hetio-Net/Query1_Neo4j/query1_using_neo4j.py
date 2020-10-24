from py2neo import Graph, NodeMatcher
from py2neo.data import Node, Relationship
from py2neo.ogm import *
import csv
from tkinter import *
import networkx as nx
import matplotlib.pyplot as plt
G = nx.DiGraph()

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

######################################################################
####### Breaking down tsv file and store into Neo4j Database #########
######################################################################

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


######################################################################
############################ Query 1##################################
######################################################################

# Given a disease id, 
# what is its name, 
# what are drug names that can treat or palliate this disease, 
# what are gene names that cause this disease, 
# and where this disease occurs? 
# Obtain and output this information in a single query.
def queryDisease(diseaseID):
    global window
    query1_message = Text(window, width=100, height=10, wrap=WORD, background="white")
    query1_message.grid(row=16, column=0, columnspan=2, sticky=W)
    query = f"""
        MATCH (c:Compound)-[:treats|palliates]->(d:Disease {{id: "{diseaseID}"}})
        OPTIONAL MATCH (d:Disease {{id: "{diseaseID}"}})-[:associates|upregulates|downregulates]->(g:Gene)
        OPTIONAL MATCH (d:Disease {{id: "{diseaseID}"}})-[:localizes]->(a:Anatomy)
        RETURN d.name, c.name, g.name, a.name
    """
    results = graph.run(query).data()
    if not results:
        #print("No record found")
        query1_message.insert(END, "No record found. Please re-enter.")
    else:
        compound_names=set()
        gene_names=set()
        anatomy_names=set()

        for result in results:
            # avoid adding "None" node to the graph
            if(str(result['c.name'])!="None"):
                compound_names.add(result['c.name'])
            if(str(result['g.name'])!="None"):
                gene_names.add(result['g.name'])
            if(str(result['a.name'])!="None"):
                anatomy_names.add(result['a.name'])

        query1_result = f"""
            Disease ID: {diseaseID}
            Disease Name: {result['d.name']}
            Drugs that treat/palliates this disease: {compound_names}
            Genes that cause cause this disease: {gene_names}
            This disease occurs at: {anatomy_names}
        """
        
        query1_message.insert(END, query1_result)
        
        
        disease = str(result['d.name'] +"\n"+diseaseID )
        ######################################################################
        #### Creating a graph as an output using networkx and matplotlib #####
        ######################################################################

        # avoid adding "None" node to the graph
        if(len(compound_names)!=0):
            for compound_name in compound_names:
                G.add_edge((str)(compound_name),disease)
        if(len(gene_names)!=0):
            for gene_name in gene_names:
                G.add_edge(disease, (str)(gene_name))
        if(len(anatomy_names)!=0):
            for anatomy_name in anatomy_names:
                G.add_edge(disease, (str)(anatomy_name))

        pos = nx.spring_layout(G)

        # drawing edges and nodes
        nx.draw(G,pos,edge_color='red',width=1,linewidths=1, node_size=2000,node_color='#9999FF',alpha=0.8,arrowsize=20, arrows= True,labels={node:node for node in G.nodes()  })
        

        # adding edge label to each edge
        if(len(compound_names)!=0):
            for compound_name in compound_names:
                nx.draw_networkx_edge_labels(G,pos,edge_labels={((str)(compound_name), disease):'treats/paliates'},font_color='red')
        if(len(gene_names)!=0):
            for gene_name in gene_names:
                nx.draw_networkx_edge_labels(G,pos,edge_labels={(disease, (str)(gene_name)):'associates/downregulates/upregulates'},font_color='red')
        if(len(anatomy_names)!=0):
            for anatomy_name in anatomy_names:
                nx.draw_networkx_edge_labels(G,pos,edge_labels={(disease,(str)(anatomy_name)):'localizes'},font_color='red')
        
        

        
        # if(compound_name!="None"):
        #   nx.draw_networkx_edge_labels(G,pos,edge_labels={(compound_name, result['d.name']+ "\n"+diseaseID):'treats/paliates'},font_color='red')
        # if(gene_name!="None"):
        #   nx.draw_networkx_edge_labels(G,pos,edge_labels={(gene_name,result['d.name']+"\n"+diseaseID):'associates'},font_color='red')
        # if(anatomy_name!="None"):
        #   nx.draw_networkx_edge_labels(G,pos,edge_labels={(result['d.name']+"\n"+diseaseID,anatomy_name):'localizes'},font_color='red')
        # plt.show()



        # query1_result = f"""
        #   Disease ID: {diseaseID}
  #         Disease Name: {result['d.name']}
  #         Drugs that treat/palliates this disease: {compound_name}
  #         Genes that cause cause this disease: {gene_name}
  #         This disease occurs at: {anatomy_name}
        # """
     #        # print(f"\t{result['d.name']}")
     #        # print(f"\t{result['c.name']}")
     #        # print(f"\t{result['g.name']}")
     #        # print(f"\t{result['a.name']}")
        # query1_message.insert(END, query1_result)
  


# We assume that a compound can treat a disease 
# if the compound or its resembled compound up-regulates/down-regulates a gene, 
# but the location down-regulates/up-regulates the gene in an opposite direction where the disease occurs. 
# Find all compounds that can treat a new disease name 
# (i.e. the missing edges between compound and disease excluding existing drugs). 
# Obtain and output all drugs in a single query.
def queryCompound(compound):
    query = f"""
        MATCH (c)-[:upregulates]->(:Gene)<-[:downregulates]-(d:Disease)
        WHERE (c.name =  "{compound}" OR ((c)-[:resembles]->(:Compound {{name: "{compound}"}}))) AND NOT (c)-[:treats]->(d)
        OPTIONAL MATCH (c)-[:downregulates]->(:Gene)<-[:upregulates]-(d:Disease)
  		WHERE (c.name =  "{compound}" OR ((c)-[:resembles]->(:Compound {{name: "{compound}"}}))) AND NOT (c)-[:treats]->(d)
        RETURN DISTINCT c.name, d.name
    """
 
    results = graph.run(query).data()
    if not results:
        print("No results found")
    else:
        print("Compound-Disease pairs:")
        for result in results:
            print(f"\t{result['c.name']}-{result['d.name']}")

######################################################################
##################### functions for GUI part #########################
######################################################################
def showGraph():
    plt.show()

def query1():
    global textentry
    disease_id = textentry.get()
    queryDisease(disease_id)
    Button(window, text="VIEW GRAPH", width=10, command=showGraph) .grid(row=13, column=0, sticky=W)


def choiceClick():
    global textentry
    global disease_id
    global choice_message
    choice = textentry.get() #this will collect the text from the text entry
    choice_message.delete(0.0, END) # clear the text in textentry
    # while(choice != "A" and choice != "B"):
 #         choice = input("Invalid Choice. Please re-enter << ")
    
    if choice == 'A':
        choice_message.insert(END, "CHOICE A was entered.")
        Label(window, text="Please enter a disease ID: ", bg="#856ff8", fg="white", font="none 12 bold") .grid(row=9,column=0, sticky=W)
        textentry = Entry(window, width=20, bg="white")
        textentry.grid(row=10,column=0,sticky=W)
        Button(window, text="SUBMIT", width=6, command=query1) .grid(row=12, column=0, sticky=W)        
    else:
        choice_message.insert(END, "Invalid choice. Please re-enter.")
    # query = input("Please enter a disease ID: ")
    # while(not queryDisease(query)):
    #   query = input ("Invalid ID was entered. Please re-enter: ")
    

# close the window
def closeWindow():
    window.destroy()
    exit()

######################################################################
##################### Creating GUI using tkinter######################
######################################################################

graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))
graph.delete_all()

window = Tk()
window.title("Big Data Technology Project I by Yiheng & Liulan ")
window.configure(background="#856ff8")


readNodes()
readEdges()


#https://www.youtube.com/watch?v=_lSNIrR1nZU
#adding image
#photo1 = PhtoImage(file=" ")
Label(window, text=MESSAGAE, bg="#856ff8",fg="white", font="none 12 bold") .grid(row=0,column=0, sticky=W)
# Enter choice eiher 'A' or 'B'
Label(window, text="Please enter your choice: ", bg="#856ff8", fg="white", font="none 12 bold") .grid(row=2,column=0, sticky=W)
textentry = Entry(window, width=20,bg="white")
textentry.grid(row=4,column=0,sticky=W)
Button(window, text="SUBMIT CHOICE", width=14, command=choiceClick) .grid(row=6, column=0, sticky=W)
choice_message = Text(window, width=40, height=1, wrap=WORD, background="white")
choice_message.grid(row=7, column=0, columnspan=2, sticky=W)


# Exit button
Button(window, text="Exit", width=10, command=closeWindow) .grid(row=42, column=0, sticky=E)


window.mainloop()


############## Without GUI #############################

# choice = input("Please enter your choice: ")
# while(choice != "A" and choice != "B"):
#     choice = input("Invalid Choice. Please re-enter << ")


# if choice == 'A':
#     query = input("Please enter a disease ID: ")
#     while(not queryDisease(query)):
#       query = input ("Invalid ID was entered. Please re-enter: ")

# if choice == 'B':
#     query = input("Please enter a compound name: ")
#     queryCompound(query)


# if __name__ == "__main__":
#     main()


############Liulan's running command reference###########
# sudo systemctl status neo4j.service
# sudo service neo4j start

# DISPLAY=:0 python3 setting-up-py2neo.py
#xming
