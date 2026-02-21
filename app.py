import streamlit as st
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains.question_answering import load_qa_chain
from langchain_core.prompts import PromptTemplate
# 1. Load the secret API key from your .env file
load_dotenv()

# Configure the Google GenAI library with the key from your .env file
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 2. Function to extract text from the uploaded PDFs
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            # Extract text page by page and add it to our main string
            text += page.extract_text()
    return text

# 3. Function to split the massive text into smaller, manageable chunks
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=10000,  # Number of characters per chunk
        chunk_overlap=1000 # Overlap ensures we don't cut a sentence in half
    )
    chunks = text_splitter.split_text(text)
    return chunks
# 4. Function to convert text to vectors and store them in a database
def get_vector_store(text_chunks):
    # We use Google's embedding model to convert words into numerical vectors
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # FAISS creates a highly optimized database out of our chunks
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    
    # Save this database locally in our folder so we don't have to re-read the PDF every time
    vector_store.save_local("faiss_index")
    
    # 5. Function to set the rules for the AI (Prompt Engineering)
def get_conversational_chain():
    # This is the strict instruction template. It prevents "Hallucination"
    prompt_template = """
    Answer the question as detailed as possible from the provided context. 
    If the answer is not in the provided context, just say, "The answer is not available in the provided document." 
    Do NOT provide a wrong answer or guess from outside knowledge.\n\n
    Context:\n {context}\n
    Question: \n{question}\n
    Answer:
    """
    
    # We use Gemini Pro with a low temperature (0.3) so it stays factual and logical, not creative
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)    
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    
    return chain

# 6. Function to handle what happens when the user types a question
def user_input(user_question):
    # We need the same embedding model to convert the user's question into numbers
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # Load the FAISS database we created in Step 3
    # Note: allow_dangerous_deserialization=True is required for local FAISS loading
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    
    # Do a "Similarity Search": Find the paragraphs in the PDF that match the question
    docs = new_db.similarity_search(user_question)
    
    # Get our AI chain
    chain = get_conversational_chain()
    
    # Pass the matching paragraphs (docs) and the user's question to the AI
    response = chain.invoke(
        {"input_documents": docs, "question": user_question},
        return_only_outputs=True
    )
    
    # Display the final answer on the screen
    st.write("Reply: ", response["output_text"])
    
    # 7. The Main Streamlit UI App
def main():
    # Set the page layout to wide and give it a professional title
    st.set_page_config(page_title="AuditSense AI", page_icon="📑", layout="wide")

    # Injecting Custom CSS for a sleek, animated gradient title
    st.markdown("""
    <style>
    .title-animate {
        background: linear-gradient(-45deg, #000000, #86BC25, #000000); /* Deloitte Green & Black theme */
        background-size: 300% 300%;
        animation: gradient 6s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3.5rem;
        text-align: center;
        padding-bottom: 20px;
    }
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    /* Adding a subtle hover effect to the upload box */
    .stFileUploader > div > div {
        transition: transform 0.3s ease-in-out;
    }
    .stFileUploader > div > div:hover {
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

    # Render the animated title
    st.markdown('<h1 class="title-animate">AuditSense: Enterprise Document AI</h1>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Intelligent RAG Pipeline for Financial Audits</p>", unsafe_allow_html=True)
    st.write("---")

    # Main Chat Area
    # Main Chat Area
    user_question = st.text_input("Ask a question about the uploaded audit reports (e.g., 'What is the total revenue?'):")

    if user_question:
        # SAFETY CHECK 3: Does the database folder actually exist yet?
        if not os.path.exists("faiss_index"):
            st.warning("⚠️ Stop! Please upload and process a PDF from the sidebar first. The AI needs a document to read before it can answer questions.")
        else:
            # Animated spinner while the AI is "thinking"
            with st.spinner("Scanning vector database and generating response..."):
                user_input(user_question)
    # The Sidebar for Document Uploading
   # The Sidebar for Document Uploading
    with st.sidebar:
        st.title("📁 Document Upload")
        st.write("Upload PDF contracts, impact reports, or financial statements here.")
        
        pdf_docs = st.file_uploader("Drop your PDFs here", accept_multiple_files=True)
        
        if st.button("Process Documents"):
            # SAFETY CHECK 1: Did the user actually upload a file?
            if not pdf_docs:
                st.warning("⚠️ Please upload at least one PDF file before processing.")
            else:
                with st.spinner("Extracting text and building AI embeddings..."):
                    raw_text = get_pdf_text(pdf_docs)
                    
                    # SAFETY CHECK 2: Is the PDF completely blank or just images?
                    if not raw_text.strip():
                        st.error("❌ Could not read text from this PDF. It might be a scanned image.")
                    else:
                        text_chunks = get_text_chunks(raw_text)
                        get_vector_store(text_chunks)
                        st.success("✅ Database created successfully! You can now ask questions.")
                        st.balloons()

# This ensures the app runs when you execute the script
if __name__ == "__main__":
    main()
