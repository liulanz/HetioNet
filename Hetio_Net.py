from py2neo import Graph, NodeMatcher
from py2neo.data import Node, Relationship
from py2neo.ogm import *
from pymongo import MongoClient
import csv
from tkinter import *
import networkx as nx
import matplotlib.pyplot as plt


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
########################### setting things up ########################
######################################################################

# neo4j database connection
graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))
# graph.delete_all()    # delete existing data 

# set up graph for output using networkx
G = nx.DiGraph()

# Mongodb connection to cluster
cluster = MongoClient("mongodb+srv://mongodb:mongodb@cluster0.vnvto.mongodb.net/<dbname>?retryWrites=true&w=majority")
db1 = cluster["HetioNet"]
collection1 = db1["HetioNet"]
# collection1.delete_many({})    # delete existing data 

db = cluster["HetioNet-longdata"]
collection = db["HetioNet-longdata"]
# collection.delete_many({})     # delete existing data 


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

######################################################################
###################### Storing nodes into databases ##################
######################################################################

def readNodes():
    global collection
    # nodes_tsv_file = open("sample_nodes.tsv")
    nodes_tsv_file = open("nodes.tsv")
    nodes_read_tsv = csv.reader(nodes_tsv_file, delimiter = "\t")
    next(nodes_read_tsv, None) # skip first row
    for row in nodes_read_tsv:
        ID = row[0].split("::")[1]
        Name = row[1]
        kind = row[2]
        node = Node(kind, name = Name, id = ID)
        # store into neo4j
        graph.create(node)
        # store into mongodb
        document = {"_id":(str)(ID), "type":(str)(kind),"name": (str)(Name) }
        collection.insert_one(document)

    nodes_tsv_file.close()

######################################################################
###################### Storing edges into databases ##################
######################################################################

def readEdges():
#    edges_tsv_file = open("sample_edges.tsv")
    edges_tsv_file = open("edges.tsv")
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

        # store into neo4j
        query = f"""
        MATCH (a:{source_type}),(b:{target_type})
        WHERE a.id = '{source_ID}' AND b.id = '{target_ID}'
        CREATE (a)-[r: {relationship}]->(b)
        """
        graph.run(query)

        # store into mongodb
        source = collection.find_one({'_id':source_ID})
        target = collection.find_one({'_id':target_ID})

        source_relationship = relationship+"->"
        collection.update_one({'_id':source_ID},{'$push':{source_relationship:target['name']}})
        target_relationship = "->"+relationship
        collection.update_one({'_id':target_ID},{'$push':{target_relationship:source['name']}})

    edges_tsv_file.close()


######################################################################
############################ Query 1 #################################
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

    ######################################################################
    ########################## Query 1 using Mongodb #####################
    ######################################################################
    
    results = collection.find({'_id': diseaseID}, {'name':1, '->treats': 1, '->palliates': 1, 'associates->': 1, 'downregulates->': 1, 'upregulates->': 1, 'localizes->': 1})
    
    if not results:
        query1_message.insert(END, "No record found. Please re-enter.")
    else:
        for i in results:
            res = i
            # print(f"\t{res}")

    compound_names=set()
    gene_names=set()
    anatomy_names=set()

    if '->treats' in res:
        for i in res['->treats']:
            compound_names.add(i)

    if '->palliates' in res:
        for i in res['->palliates']:
            compound_names.add(i)

    if 'associates->' in res:
        for i in res['associates->']:
            gene_names.add(i)
       
    if 'downregulates->' in res:
        for i in res['downregulates->']:
            gene_names.add(i)

    if 'upregulates->' in res:
        for i in res['upregulates->']:
            gene_names.add(i)

    if 'localizes->' in res:
        for i in res['localizes->']:
            anatomy_names.add(i)

    query1_result = f"""
        Disease ID: {diseaseID}
        Disease Name: {res['name']}
        Drugs that treat/palliates this disease: {compound_names}
        Genes that cause cause this disease: {gene_names}
        This disease occurs at: {anatomy_names}
    """
    query1_message.insert(END, query1_result)

    disease = str(res['name']+"\n"+diseaseID)
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

    ######################################################################
    ########################## Query 1 using Neo4j #######################
    ######################################################################

    # query = f"""
    #     MATCH (c:Compound)-[:treats|palliates]->(d:Disease {{id: "{diseaseID}"}})
    #     OPTIONAL MATCH (d:Disease {{id: "{diseaseID}"}})-[:associates|upregulates|downregulates]->(g:Gene)
    #     OPTIONAL MATCH (d:Disease {{id: "{diseaseID}"}})-[:localizes]->(a:Anatomy)
    #     RETURN d.name, c.name, g.name, a.name
    # """
    # results = graph.run(query).data()
    # if not results:
    #     query1_message.insert(END, "No record found. Please re-enter.")
    # else:
    #     compound_names=set()
    #     gene_names=set()
    #     anatomy_names=set()

    #     for result in results:
    #         # avoid adding "None" node to the graph
    #         if(str(result['c.name'])!="None"):
    #             compound_names.add(result['c.name'])
    #         if(str(result['g.name'])!="None"):
    #             gene_names.add(result['g.name'])
    #         if(str(result['a.name'])!="None"):
    #             anatomy_names.add(result['a.name'])

    #     query1_result = f"""
    #         Disease ID: {diseaseID}
    #         Disease Name: {result['d.name']}
    #         Drugs that treat/palliates this disease: {compound_names}
    #         Genes that cause cause this disease: {gene_names}
    #         This disease occurs at: {anatomy_names}
    #     """
        
    #     query1_message.insert(END, query1_result)
        
        
    #     disease = str(result['d.name'] +"\n"+diseaseID )
    #     G.clear()
    #     # avoid adding "None" node to the graph
    #     if(len(compound_names)!=0):
    #         for compound_name in compound_names:
    #             G.add_edge((str)(compound_name),disease)
    #     if(len(gene_names)!=0):
    #         for gene_name in gene_names:
    #             G.add_edge(disease, (str)(gene_name))
    #     if(len(anatomy_names)!=0):
    #         for anatomy_name in anatomy_names:
    #             G.add_edge(disease, (str)(anatomy_name))

    #     pos = nx.spring_layout(G)

    #     # drawing edges and nodes
    #     nx.draw(G,pos,edge_color='red',width=1,linewidths=1, node_size=2000,node_color='#9999FF',alpha=0.8,arrowsize=20, arrows= True,labels={node:node for node in G.nodes()  })
        

    #     # adding edge label to each edge
    #     if(len(compound_names)!=0):
    #         for compound_name in compound_names:
    #             nx.draw_networkx_edge_labels(G,pos,edge_labels={((str)(compound_name), disease):'treats/paliates'},font_color='red')
    #     if(len(gene_names)!=0):
    #         for gene_name in gene_names:
    #             nx.draw_networkx_edge_labels(G,pos,edge_labels={(disease, (str)(gene_name)):'associates/downregulates/upregulates'},font_color='red')
    #     if(len(anatomy_names)!=0):
    #         for anatomy_name in anatomy_names:
    #             nx.draw_networkx_edge_labels(G,pos,edge_labels={(disease,(str)(anatomy_name)):'localizes'},font_color='red')

  

######################################################################
############################ Query 2 #################################
######################################################################

# We assume that a compound can treat a disease 
# if the compound or its resembled compound up-regulates/down-regulates a gene, 
# but the location down-regulates/up-regulates the gene in an opposite direction where the disease occurs. 
# Find all compounds that can treat a new disease name 
# (i.e. the missing edges between compound and disease excluding existing drugs). 
# Obtain and output all drugs in a single query.

def queryCompound(compound):
    global window
    query2_message = Text(window, width=100, height=10, wrap=WORD, background="white")
    query2_message.grid(row=16, column=0, columnspan=2, sticky=W)
    
    query = f"""
        MATCH (c)-[:upregulates]->(:Gene)<-[:downregulates]-(d:Disease)
        WHERE ((c:Compound) OR ((c)-[:resembles]->(:Compound))) AND NOT (c)-[:treats]->(d)
        OPTIONAL MATCH (c)-[:downregulates]->(:Gene)<-[:upregulates]-(d:Disease)
        WHERE ((c:Compound) OR ((c)-[:resembles]->(:Compound))) AND NOT (c)-[:treats]->(d)
        RETURN DISTINCT c.name, d.name
    """

    results = graph.run(query).data()
    if not results:
        query2_message.insert(END, "No record found. Please re-enter.")
    else:
        compound_disease_pairs=[]
        compound_names=[]
        disease_names=[]

        for result in results:
            # avoid adding "None" node to the graph
            if(str(result['c.name'])!="None"):
                compound_disease_pairs.append(result['c.name'] + ' - ' + result['d.name'])
                compound_names.append(result['c.name'])
            if(str(result['d.name'])!="None"):
                disease_names.append(result['d.name'])
        query2_message.insert(END, 'Compound-Disease pairs:' + '\n') 
        for pair in compound_disease_pairs:
            query2_message.insert(END, pair + '\n') 


        # G.clear()



        # if(len(compound_names)!=0):
        #     for compound_name in compound_names:
        #         G.add_edge((str)(compound_name),disease)
        # if(len(gene_names)!=0):
        #     for gene_name in gene_names:
        #         G.add_edge(disease, (str)(gene_name))
        # if(len(anatomy_names)!=0):
        #     for anatomy_name in anatomy_names:
        #         G.add_edge(disease, (str)(anatomy_name))

        # pos = nx.spring_layout(G)

        # # drawing edges and nodes
        # nx.draw(G,pos,edge_color='red',width=1,linewidths=1, node_size=2000,node_color='#9999FF',alpha=0.8,arrowsize=20, arrows= True,labels={node:node for node in G.nodes()  })
        

        # # adding edge label to each edge
        # if(len(compound_names)!=0):
        #     for compound_name in compound_names:
        #         nx.draw_networkx_edge_labels(G,pos,edge_labels={((str)(compound_name), disease):'treats/paliates'},font_color='red')
        # if(len(gene_names)!=0):
        #     for gene_name in gene_names:
        #         nx.draw_networkx_edge_labels(G,pos,edge_labels={(disease, (str)(gene_name)):'associates/downregulates/upregulates'},font_color='red')
        # if(len(anatomy_names)!=0):
        #     for anatomy_name in anatomy_names:
        #         nx.draw_networkx_edge_labels(G,pos,edge_labels={(disease,(str)(anatomy_name)):'localizes'},font_color='red')



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

def query2():
    global textentry
    compound_name = textentry.get()
    queryCompound(compound_name)
    Button(window, text="VIEW GRAPH", width=10, command=showGraph) .grid(row=13, column=0, sticky=W)

def choiceClick():
    global choice_entered
    global disease_id
    global choice_message
    choice = choice_entered.get() #this will collect the text from the text entry
    choice_message.delete(0.0, END) # clear the text in textentry

    if choice == 'A':
        choice_message.insert(END, "CHOICE A was entered.")
        Label(window, text="Please enter a disease ID: ", bg="#856ff8", fg="white", width=30,font="none 12 bold") .grid(row=9,column=0, sticky=W)
        textentry = Entry(window, width=20, bg="white")
        textentry.grid(row=10,column=0,sticky=W)
        Button(window, text="SUBMIT", width=6, command=query1) .grid(row=12, column=0, sticky=W)    
    elif choice == 'B':    
        choice_message.insert(END, "CHOICE B was entered.")
        Label(window, text="Please enter a compound name: ", bg="#856ff8", fg="white", width=30, font="none 12 bold") .grid(row=9,column=0, sticky=W)
       
        textentry = Entry(window, width=20, bg="white")
        textentry.grid(row=10,column=0,sticky=W)
        Button(window, text="SUBMIT", width=6, command=query2) .grid(row=12, column=0, sticky=W)   
    else:
        choice_message.insert(END, "Invalid choice. The choice is either 'A' or 'B'. Please re-enter.")
    

# close the window
def closeWindow():
    window.destroy()
    exit()

######################################################################
##################### Creating GUI using tkinter######################
######################################################################

window = Tk()
window.title("Big Data Technology Project I by Yiheng & Liulan ")
window.configure(background="#856ff8")


#readNodes()
#readEdges()


#https://www.youtube.com/watch?v=_lSNIrR1nZU
#adding image
#photo1 = PhtoImage(file=" ")
Label(window, text=MESSAGAE, bg="#856ff8",fg="white", font="none 12 bold") .grid(row=0,column=0, sticky=W)
# Enter choice eiher 'A' or 'B'
Label(window, text="Please enter your choice: ", bg="#856ff8", fg="white", font="none 12 bold") .grid(row=2,column=0, sticky=W)
choice_entered = Entry(window, width=20,bg="white")
choice_entered.grid(row=4,column=0,sticky=W)
Button(window, text="SUBMIT CHOICE", width=14, command=choiceClick) .grid(row=6, column=0, sticky=W)
choice_message = Text(window, width=80, height=1, wrap=WORD, background="white")
choice_message.grid(row=7, column=0, columnspan=2, sticky=W)


# Exit button
Button(window, text="Exit", width=10, command=closeWindow) .grid(row=42, column=0, sticky=E)


window.mainloop()


