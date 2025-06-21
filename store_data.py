import os
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from load_files import load_repo_files
from tqdm import tqdm

# Load documents from your repo
docs = load_repo_files("/Users/examplerepo/golang_test/learning-go")
print(f"\n Loaded {len(docs)} raw documents")

if not docs:
    raise ValueError(" No documents found! Check your load_files.py logic.")

# Split documents
text_splitter = RecursiveCharacterTextSplitter.from_language(
    language="go",
    chunk_size=1500,
    chunk_overlap=200
)
docs_split = text_splitter.split_documents(docs)
print(f" Split into {len(docs_split)} chunks")

# Extract content & metadata
texts = [doc.page_content for doc in docs_split]
metadatas = [doc.metadata for doc in docs_split]

# Embedding model
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
vector_store = Chroma(persist_directory="chroma_db", embedding_function=embedding_model)

# Use batching to avoid hitting token limits
def batch_generator(items, batch_size):
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

# Estimate tokens per chunk (conservative average ~600 tokens)
MAX_TOKENS = 300000
AVG_TOKENS_PER_DOC = 600
MAX_DOCS_PER_BATCH = MAX_TOKENS // AVG_TOKENS_PER_DOC

all_embeddings = []
all_metadatas = []

vectorstore = Chroma(
    embedding_function=embedding_model,
    persist_directory="./chroma_db",
    collection_name="project_embeddings_v2",  # new name
)


print(" Storing documents in ChromaDB with batching...")

for text_batch, metadata_batch in tqdm(
    zip(batch_generator(texts, MAX_DOCS_PER_BATCH),
        batch_generator(metadatas, MAX_DOCS_PER_BATCH)),
    total=(len(texts) // MAX_DOCS_PER_BATCH) + 1
):
    vectorstore.add_texts(
        texts=text_batch,
        metadatas=metadata_batch
    )

vectorstore.persist()
print(" All documents embedded & stored in ChromaDB!")
