try:
    from langchain_classic.chains.question_answering import load_qa_chain
    print("Found load_qa_chain")
except ImportError as e:
    print(f"Error importing load_qa_chain: {e}")

try:
    from langchain_core.prompts import PromptTemplate
    print("Found PromptTemplate")
except ImportError as e:
    print(f"Error importing PromptTemplate: {e}")
