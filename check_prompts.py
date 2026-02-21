try:
    from langchain_core.prompts import PromptTemplate
    print("Found PromptTemplate in langchain_core")
except ImportError:
    print("Not in core")

try:
    from langchain_classic.prompts import PromptTemplate
    print("Found PromptTemplate in langchain_classic")
except ImportError:
    print("Not in classic")
