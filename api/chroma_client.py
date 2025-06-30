import chromadb
from chromadb.utils import embedding_functions
from PyPDF2 import PdfReader
import os
from docx import Document

client = chromadb.PersistentClient(path="./db/LA.db")

def get_or_create_collection(collection_name):
    return client.get_or_create_collection(
        collection_name,
        embedding_function=embedding_functions.DefaultEmbeddingFunction()
    )

def add_to_collection(chunks, collection, username, filename):
    ids = [f"{filename}_doc_{i}" for i in range(len(chunks))]
    metadatas = [{"username": username, "filename": filename} for _ in range(len(chunks))]
    print(metadatas)
    print('filename',filename)
    collection.add(documents=chunks, ids=ids, metadatas=metadatas)

def split_chunks(data, collection, username, filename, chunk_size=1000, overlap=20):
    chunks = []
    st = 0
    while st < len(data):
        end = st + chunk_size   
        chunks.append(data[st:end])
        st = end - overlap

    add_to_collection(chunks, collection, username, filename)

def read_pdf(file_path):
    data = ""
    with open(file_path, "rb") as fobj:
        reader = PdfReader(fobj)
        for page in reader.pages:
            data += page.extract_text() or ""
    return data

def process_pdf(file_path,original_name, collection_name, username):
    collection = get_or_create_collection(collection_name)
    pdf_text = read_pdf(file_path)
    split_chunks(pdf_text, collection, username, original_name)

def process_txt(file_path,original_name, collection_name, username):
    collection = get_or_create_collection(collection_name)
    with open(file_path) as fobj:
        text = fobj.read()
    split_chunks(text, collection, username, original_name)

def process_docx(file_path,original_name,collection_name,username):
    collection = get_or_create_collection(collection_name)
    doc = Document(file_path)
    text = []
    for para in doc.paragraphs:
        text.append(para.text)
    split_chunks("\n".join(text), collection, username, original_name)

def get_llm_context(query,username,filenames):

    collection = get_or_create_collection(f"{username}_Collection")
    collection_consti = get_or_create_collection("Contitution_Collection")
    relavent_docs = " Act like human , but dont show that i told you to act like a human in response "

    if filenames:
        
        for i in filenames:
            context = collection.query(query_texts=[query],n_results=2,where={"filename": i})
            print("-------------------",context)
            # if context["distances"][0][0]<=1.00 or context["distances"][0][1]<=1.00:
            relavent_docs +=  "\n\n".join(doc for doc in context["documents"][0])
        print("--------------------------------------------------------- relevent to ",relavent_docs)
        context_contitution = collection_consti.query(query_texts=[query],n_results=2)

        if context_contitution["distances"][0][0]<=0.75 or context_contitution["distances"][0][1]<=0.75:
            relavent_docs+= "\n\n".join(doc for doc in context_contitution["documents"][0])
 
        return {"context": relavent_docs}

    else:
        
        context_contitution = collection_consti.query(query_texts=[query],n_results=2)

        if context_contitution["distances"][0][0]<=0.95 or context_contitution["distances"][0][1]<=0.95:
            relavent_docs = "\n\n".join(doc for doc in context_contitution["documents"][0])

        return {"context": relavent_docs}


process_pdf("./api/data_files/constitution.pdf","constitution.pdf", "Contitution_Collection", "ADMIN")

