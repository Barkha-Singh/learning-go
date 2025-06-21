from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.prompts import PromptTemplate

from generate_tests import generate_test_cases  # <<=== imported test generator

# === Embeddings and VectorStore ===
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
vector_store = Chroma(persist_directory="chroma_db", embedding_function=embedding_model)
retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 8})

# === Prompt for general Q&A ===
qa_prompt = PromptTemplate.from_template("""
You are an expert coding assistant for a Java project. Use the following file contents to answer the user's question.
                                         
Context:
{context}

Question: {question}

Answer in helpful, concise, and code-savvy language:
""")

# === Chains ===
llm = ChatOpenAI(model="o3")

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
    chain_type="stuff",
    chain_type_kwargs={"prompt": qa_prompt}
)

# === Functions ===
def query_repo(question):
    result = qa_chain.invoke({"query": question})
    print("\n Answer:\n", result["result"])

    source_files = {doc.metadata.get("source") for doc in result["source_documents"]}
    print("\n Source files used:")
    for source in sorted(source_files):
        print(f" - {source}")

    print("\n Top chunks preview:")
    for i, doc in enumerate(result["source_documents"][:3]):
        print(f"\n--- Chunk {i+1} ({doc.metadata.get('source')}) ---\n")
        print(doc.page_content[:500])

def handle_test_request(question):
    test_result = generate_test_cases(question)

    print(f"\n[✓] Detected Framework: {test_result['framework']}")
    print("\nSuggested Test Cases:\n", test_result["result"])

    print("\nSource files used:")
    for source in test_result["sources"]:
        print(f" - {source}")

    print("\nRelevant Chunks:")
    for i, doc in enumerate(test_result["chunks"]):
        print(f"\n--- Chunk {i+1} ({doc.metadata.get('source')}) ---\n")
        print(doc.page_content[:500])


# === CLI Loop ===
if __name__ == "__main__":
    while True:
        query = input("\nAsk about the repo (or type 'exit'): ")
        if query.lower() == "exit":
            break

        if any(word in query.lower() for word in ["test", "unit test", "integration", "write tests", "generate test", "pytest", "unittest"]):
            handle_test_request(query)
        else:
            query_repo(query)
