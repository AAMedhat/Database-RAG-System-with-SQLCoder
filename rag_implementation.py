from langchain_community.llms import HuggingFacePipeline
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

from sqlalchemy import create_engine, text
import os
import tempfile
import torch
import gc

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig

# Check if GPU is available
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Database connection
DATABASE_URL = "postgresql://postgres:01154555448963@localhost:5432/test_db"
engine = create_engine(DATABASE_URL)

# Initialize local LLM using defog/sqlcoder-7b-2
def initialize_llm():
    model_id = "defog/sqlcoder-7b-2"
    
    # Check for CUDA availability
    use_gpu = torch.cuda.is_available()
    device_to_use = "cuda" if use_gpu else "cpu"
    print(f"Using device: {device_to_use}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    # Use simple half-precision loading for GPU (works better on Windows)
    if use_gpu:
        try:
            print("Loading model with GPU acceleration using half precision...")
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map="auto",
                torch_dtype=torch.float16  # Use half precision instead of 4-bit quantization
            )
            print("Successfully loaded model with GPU acceleration and half precision")
        except Exception as e:
            print(f"Error loading with GPU acceleration: {e}")
            print("Falling back to CPU model")
            model = AutoModelForCausalLM.from_pretrained(
                model_id, 
                device_map="auto", 
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
    else:
        # If no GPU, load the model with standard precision
        model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            device_map="auto", 
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )
    
    # Optimize pipeline configuration
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=512,
        do_sample=True,
        temperature=0.7,
        top_p=0.95,
        repetition_penalty=1.1,
        device_map="auto"
    )
    
    llm = HuggingFacePipeline(pipeline=pipe)
    return llm

# Initialize embeddings with caching
_embeddings_cache = {}

def initialize_embeddings():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L12-v2",
        model_kwargs={'device': device},
        cache_folder=os.path.join(tempfile.gettempdir(), "sentence_transformers_cache")
    )
    return embeddings

# Create vector store from schema file with caching
_vector_store = None

def create_vector_store():
    global _vector_store
    
    # Return cached vector store if available
    if _vector_store is not None:
        return _vector_store
    
    # Create a persistent directory for the Chroma database
    persist_directory = os.path.join(tempfile.gettempdir(), "chroma_db")
    
    # Check if the vectorstore already exists
    if os.path.exists(persist_directory):
        print("Loading existing vector store...")
        embeddings = initialize_embeddings()
        _vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings
        )
        return _vector_store
    
    with open('database/schema.sql', 'r') as f:
        schema_text = f.read()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_text(schema_text)

    embeddings = initialize_embeddings()
    
    # Create and persist the Chroma vector store
    _vector_store = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    # Persist the vector store to disk
    if hasattr(_vector_store, 'persist'):
        _vector_store.persist()
    
    return _vector_store

# Generate SQL query from NL
def create_sql_query(question: str, vector_store) -> str:
    prompt_template = """You are an SQL expert.
Given the following PostgreSQL schema:
{context}

Generate an optimized SQL query to answer the user question:
"{question}"

Ensure that:
- Table names and column names are exactly as defined in the schema.
- Only indexed fields are used for filtering.
- The SQL query is syntactically correct for PostgreSQL.
- The query returns precise results without unnecessary joins.

Provide only the SQL query as output.
"""

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    llm = initialize_llm()
    chain = LLMChain(llm=llm, prompt=prompt)

    docs = vector_store.similarity_search(question, k=3)
    context = "\n".join([doc.page_content for doc in docs])

    response = chain.run(context=context, question=question)
    
    # Clean up memory
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
        
    return response.strip()

# Execute query
def execute_query(query: str) -> str:
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query))
            rows = result.fetchall()

            if not rows:
                return "No results found."

            formatted_result = "Results:\n"
            for row in rows:
                formatted_result += str(row) + "\n"

            return formatted_result
    except Exception as e:
        return f"Error executing query: {str(e)}"

# Main RAG class
class RAGSystem:
    def __init__(self):
        print("Initializing vector store...")
        self.vector_store = create_vector_store()
        print("Vector store initialized")
        
        print("Loading language model...")
        self.llm = initialize_llm()
        print("Language model loaded")

    def process_question(self, question: str) -> str:
        print("Generating SQL query...")
        sql_query = create_sql_query(question, self.vector_store)
        print(f"SQL Query: {sql_query}")
        
        print("Executing query...")
        query_result = execute_query(sql_query)
        
        print("Generating natural language response...")
        response_prompt = f"""Based on the following SQL query results, provide a natural language answer to the original question.

Question: {question}
SQL Query: {sql_query}
Query Results: {query_result}

Answer:"""

        response = self.llm(response_prompt)
        
        # Clean up memory
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()
            
        return response

# Entry point
def main():
    print("Initializing RAG System...")
    rag_system = RAGSystem()

    example_questions = [
        "what is the email and username of the userid 938?",
        "waht is the name and description of the catigory id 1?"
    ]

    print("RAG System initialized. You can ask questions about the database.")
    print("Example questions:")
    for q in example_questions:
        print(f"- {q}")

    while True:
        question = input("\nEnter your question (or 'quit' to exit): ")
        if question.lower() == 'quit':
            break

        try:
            print("\nProcessing your question...")
            response = rag_system.process_question(question)
            print("\nResponse:", response)
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
