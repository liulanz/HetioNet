# HetioNet

CSCI 49376: Big Data Technology

authors: Liulan Zheng, Yiheng Cen Feng

## Overview


This project stores all the nodes from nodes.tsv and stores all the relationships from edges.tsv.
We use MongoDB and Neo4j as our databases. 

Our job is to perform 2 queries through python.

**Query 1:**
Given a disease, what is its name, what are drug names that can treat or palliate this disease, 
what are gene names that cause this disease, and where this disease occurs? Obtain and output this information in a single query.

**Query 2:**
Supposed that a drug can treat a disease if the drug or its similar drugs up-regulate/down-regulate a gene, but the location 
down-regulates/up-regulates the gene in an opposite direction where the disease occurs. Find all drugs that can treat new diseases 
(i.e. the missing edges between drug and disease). Obtain and output the drug-disease pairs in a single query.


## Run


- Install Neo4j Desktop
- Set up Mongodb cluster, add link and password in python code

- start the neo4j service:
```
sudo service neo4j start
```

- connect to Neo4j database 

- Run the code
```
python Hetio_Net.py
```
