


MESSGAE = '''
CHOICE A) Given a disease, what is its name, what are drug names that can treat or
palliate this disease, what are gene names that cause this disease, and where
this disease occurs?

CHOICE B) Supposed that a drug can treat a disease if the drug or its similar drugs
up-regulate/down-regulate a gene, but the location down-regulates/up-regulates
the gene in an opposite direction where the disease occurs. Find all drugs
that can treat new diseases (i.e. the missing edges between drug and disease).

ENTER "A" for CHOICE A
ENTER "B" for CHOICE B
'''




def main():
    

    print(MESSGAE)

    choice = input("Please enter your choice: ")
    while(choice != "A" and choice != "B"):
        choice = input("Invalid Choice. Please re-enter << ")
    


    if choice == 'A':
        query = input("Please enter a disease name: ")
  

    


if __name__ == "__main__":
    main()