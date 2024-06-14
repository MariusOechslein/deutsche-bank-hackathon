from langchain.chains import RetrievalQA
from langchain_community.document_loaders import (
    DirectoryLoader,
    UnstructuredMarkdownLoader,
)
from langchain_community.vectorstores import StarRocks
from langchain_community.vectorstores.starrocks import StarRocksSettings
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain_text_splitters import TokenTextSplitter,RecursiveCharacterTextSplitter,MarkdownHeaderTextSplitter

import os
import re

from langchain_community.document_loaders import (
    DirectoryLoader,
    UnstructuredMarkdownLoader,
)

from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import chromadb

def load_md_directory(dir):

    files = os.listdir(dir)
    documents_md = []
    for i,file in enumerate(files):
        
        # print(f'reading file {i+1}/{len(files)} - {file}')
        file_r = os.path.join(dir_md,file)
        loader = UnstructuredMarkdownLoader(file_r,mode='single')
        doc = loader.load()
        documents_md.append(doc[0])
    
    print(f'{len(documents_md)} Markdown documents were loaded.')

    return documents_md

dir_md = 'files/'
documents = load_md_directory(dir_md)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=250)
splits_md = text_splitter.split_documents(documents)

print(f'Splits {len(splits_md)}')

client = chromadb.PersistentClient(path="storage")

os.environ["OPENAI_API_KEY"] = ''
EMBEDDING_MODEL = 'text-embedding-3-small'

embedding_function = OpenAIEmbeddingFunction(api_key=os.environ.get('OPENAI_API_KEY'), model_name=EMBEDDING_MODEL)

col = client.get_or_create_collection("rag_system",embedding_function = embedding_function)

col.add(ids = [f"id_{i}" for i in range(len(splits_md))],
    documents= [doc.page_content for doc in splits_md],
    metadatas=[doc.metadata for doc in splits_md])

print(f'registers {col.count()}')



