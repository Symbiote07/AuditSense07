try:
    from langchain_classic.chains.question_answering import load_qa_chain
    print("Found load_qa_chain in langchain_classic")
except ImportError as e:
    print(f"Error importing load_qa_chain from classic: {e}")
