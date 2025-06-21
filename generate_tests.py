from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain

# === Shared setup ===
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
vector_store = Chroma(persist_directory="chroma_db", embedding_function=embedding_model)
retriever = vector_store.as_retriever(search_kwargs={"k": 6})
llm = ChatOpenAI(model="o3")

# === Test prompt template with Go + gomock ===
test_prompt_template = """
You are a senior test automation engineer. Use the following context to write test cases.

Preferred Framework: {framework}

Context:
{context}

{prior_tests_block}

User Request:
{question}

Only return code in proper {framework} format:

- For Python:
    - If framework is 'unittest', use standard unittest format.
    - If framework is 'pytest', use pytest-style tests.

- For Java:
    - If framework is 'junit':
        - Use JUnit 5: @Test, @BeforeEach, assert statements, @ExtendWith.
        - For Spring Boot: use @WebMvcTest, MockMvc, @MockBean.
    - If framework is 'junit4':
        - Use JUnit 4: @Test, @Before, assert statements, @RunWith(SpringRunner.class).
        - For Spring Boot: use @RunWith(SpringRunner.class), MockMvc, @Mock.

- For Go (Golang):
    - Use the standard "testing" package.
    - Write clean, table-driven unit tests.
    - Use "github.com/golang/mock/gomock" for mocking interfaces:
        - Use gomock.NewController(t)
        - Create mocks using NewMock{{Interface}}(ctrl)
        - Use .EXPECT() for expectations
    - Prefer clear test structure: arrange, act, assert.

- For config/infrastructure files: describe logical tests, no code.

Ensure your code is clean, concise, idiomatic, and follows best practices.
"""

# === Detect framework preference ===
def detect_framework(question: str, documents) -> str:
    q = question.lower()

    has_go = any(
        doc.metadata.get("language") == "go" or doc.metadata.get("source", "").endswith(".go")
        for doc in documents
    )
    if has_go:
        return "go"

    has_java = any(
        doc.metadata.get("language") == "java" or doc.metadata.get("source", "").endswith(".java")
        for doc in documents
    )
    if has_java:
        junit4_signals = any(
            "@RunWith" in doc.page_content or "@Before" in doc.page_content or
            "import org.junit.runner" in doc.page_content
            for doc in documents
        )
        if "junit 4" in q or junit4_signals:
            return "junit4"
        return "junit"  # Default to JUnit 5

    has_py = any(
        doc.metadata.get("language") == "python" or doc.metadata.get("source", "").endswith(".py")
        for doc in documents
    )
    if has_py:
        if "unittest" in q:
            return "unittest"
        if "pytest" in q:
            return "pytest"
        # Fallback: check content
        uses_unittest = any("import unittest" in doc.page_content or "unittest.TestCase" in doc.page_content for doc in documents)
        if uses_unittest:
            return "unittest"
        return "pytest"

    # Fallback: based on user query only
    if "go" in q:
        return "go"
    if "junit 4" in q:
        return "junit4"
    if "junit" in q:
        return "junit"
    if "pytest" in q:
        return "pytest"
    if "unittest" in q or "unit test" in q:
        return "unittest"

    return "pytest"  # safest default


# === Extract prior test cases ===
def extract_prior_tests(documents):
    test_case_texts = []
    for doc in documents:
        if "test" in doc.metadata.get("source", "").lower():
            content = doc.page_content.strip()
            if (
                "def test_" in content
                or "@pytest" in content
                or "@Test" in content
                or "func Test" in content  # Golang
            ):
                test_case_texts.append(content[:800])
    return test_case_texts

# === Main callable ===
def generate_test_cases(question: str):
    relevant_docs = retriever.invoke(question)
    framework = detect_framework(question, relevant_docs)
    prior_tests = extract_prior_tests(relevant_docs)

    prior_tests_block = ""
    if prior_tests:
        joined_tests = "\n\n".join(prior_tests)
        prior_tests_block = f"The following test cases have already been written. Include these patterns or extend them:\n\n{joined_tests}"

    prompt = PromptTemplate.from_template(test_prompt_template)
    test_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)

    result = test_chain.invoke({
        "context": relevant_docs,
        "framework": framework,
        "question": question,
        "prior_tests_block": prior_tests_block
    })

    return {
        "result": result,
        "sources": sorted({doc.metadata.get("source") for doc in relevant_docs}),
        "chunks": relevant_docs[:3],
        "framework": framework,
        "prior_tests": prior_tests_block or None
    }
