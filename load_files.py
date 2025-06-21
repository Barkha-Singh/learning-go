import os
from langchain_community.document_loaders import TextLoader

def load_repo_files(repo_path):
    documents = []
    skip_dirs = {"venv", "__pycache__", ".git", ".idea", ".vscode"}

    if not os.path.exists(repo_path):
        print(f" The path '{repo_path}' does not exist!")
        return documents

    print(f"\n Scanning repo: {repo_path}\n")

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            if file.endswith((".md", ".py", ".txt", ".js", ".html", ".css", ".hcl", ".sh", ".json", ".yaml", ".yml",".java",".go")):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repo_path)
                folder = os.path.dirname(relative_path)
                ext = os.path.splitext(file)[1].lstrip(".")

                try:
                    loader = TextLoader(file_path, encoding="utf-8")
                    loaded_docs = loader.load()

                    for doc in loaded_docs:
                        doc.metadata["source"] = relative_path
                        doc.metadata["full_path"] = file_path
                        doc.metadata["language"] = ext
                        doc.metadata["type"] = (
                            "code" if ext in {"py", "js", "sh",".java",".go"} else
                            "config" if ext in {"yaml", "yml", "json", "hcl"} else
                            "markdown" if ext == "md" else
                            "text"
                        )
                        # Add LLM-friendly header
                        doc.page_content = f"# FILE: {relative_path} [{ext}]\n# FOLDER: {folder}\n\n{doc.page_content}"
                        documents.append(doc)

                    print(f" Loaded: {relative_path}")

                except Exception as e:
                    print(f" Error loading {relative_path}: {e}")

    print(f"\n Total documents loaded: {len(documents)}")
    return documents

if __name__ == "__main__":
    repo_path = "/Users/examplerepo/golang_test/learning-go"
    docs = load_repo_files(repo_path)
    print(f"\n Loaded {len(docs)} documents.")
