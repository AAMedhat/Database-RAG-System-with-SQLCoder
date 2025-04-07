# Database RAG System with SQLCoder

This project implements a Retrieval-Augmented Generation (RAG) system that uses the `defog/sqlcoder-7b-2` model to answer questions about a PostgreSQL database. The system converts natural language questions into SQL queries and provides human-readable answers.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git
- NVIDIA GPU with CUDA support (optional, but recommended)
- 16GB+ RAM

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd [repository-directory]
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix/MacOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
   - Install PostgreSQL if you haven't already
   - Update the database connection parameters in `rag_implementation.py` if needed
   - Run the database setup and population script:
```bash
python database/populate_data.py
```
   This script will automatically:
   - Create the `test_db` database if it doesn't exist
   - Create all necessary tables and indexes
   - Populate the tables with sample data

## Project Structure

```
.
├── database/
│   ├── schema.sql          # Database schema definition
│   └── populate_data.py    # Script to create and populate the database
├── rag_implementation.py   # Main RAG implementation
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Usage

1. Start the RAG system:
```bash
python rag_implementation.py
```

2. Enter your questions about the database when prompted. Example questions:
   - "What is the name and description of the category id 1?"
   - "What is the email and username of the user id 938?"

3. Type 'quit' to exit the program.

## Performance Optimizations

The system includes several optimizations for better performance on local hardware:

1. **GPU Acceleration with Half-Precision**: The SQLCoder model uses half-precision (16-bit) floating point on GPU which:
   - Reduces memory usage by ~50% compared to full precision
   - Increases inference speed significantly
   - Works efficiently on Windows without compatibility issues
   - Provides better accuracy than 4-bit quantization

2. **Vector Store Caching**:
   - Creates and persists the vector store to disk
   - Reuses the existing vector store on subsequent runs
   - Eliminates the need to recompute embeddings

3. **GPU Acceleration**: 
   - Automatically detects and utilizes GPU if available
   - Falls back to CPU with optimized settings if no GPU is present
   - Uses half-precision (FP16) for better performance on GPU

4. **Memory Management**:
   - Implements proactive garbage collection
   - Clears CUDA cache after heavy operations
   - Prevents memory leaks during long sessions

These optimizations make the system much more efficient for local deployment, especially on machines with limited resources.

## SQLCoder-7b-2 Model

This project utilizes [SQLCoder-7b-2](https://huggingface.co/defog/sqlcoder-7b-2), a powerful language model developed by Defog for natural language to SQL generation. Key features of this model include:

- **Model Size**: 6.74B parameters
- **Base Model**: Fine-tuned from CodeLlama-7B
- **Purpose**: Designed to help non-technical users understand data inside SQL databases
- **Performance**: High accuracy across various SQL query types, including:
  - Date operations (96% accuracy)
  - Group-by queries (91.4% accuracy) 
  - Joins (91.4% accuracy)
  - Ratio calculations (94.3% accuracy)
  - Where clauses (77.1% accuracy)

The model has been optimized for generating complex SQL queries from natural language questions and outperforms many larger models on SQL-specific tasks. In our implementation, we use this model with specific parameters:

```python
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=512,
    do_sample=True,
    temperature=0.7,
    top_p=0.95,
    repetition_penalty=1.1
)
```

This configuration balances between deterministic responses and creative problem-solving for SQL generation.

## Database Schema

The system uses the following tables:
- users - User information including username, email, and activity status
- products - Product details including name, price, category, and stock quantity
- orders - Order information with user references, total amount, and status
- order_items - Individual items within orders with quantity and unit price
- reviews - Product ratings and comments from users
- categories - Product categories with descriptions
- suppliers - Supplier company information and contacts
- product_suppliers - Relationship between products and their suppliers

Each table contains meaningful fields and relationships, with appropriate indexes for optimization.

## Data Generation with Faker

The project uses the [Faker](https://faker.readthedocs.io/) library to generate realistic sample data for the database. Faker is a Python package that generates fake data for various use cases:

- **User information**: Usernames, emails, full names, and timestamps
- **Product details**: Product names, descriptions, prices, and stock quantities
- **Supplier information**: Company names, contact persons, email addresses, and phone numbers
- **Review content**: Rating values and comment text
- **Address information**: Used for shipping addresses in orders

Faker ensures that the sample data is realistic and diverse, making it ideal for testing the RAG system with a variety of queries. The data generation process in `populate_data.py` is designed to be idempotent, meaning it can be run multiple times without creating duplicate entries.

## Features

- SQLCoder model for natural language to SQL conversion
- GPU acceleration with 16-bit precision (half-precision)
- Vector-based retrieval using Chroma
- Optimized for Windows compatibility
- Human-readable responses
- Comprehensive sample data generation
- Idempotent scripts (safe to run multiple times)


## Conclusion

This RAG system demonstrates how to leverage modern LLM technology for database question answering without requiring cloud services. The system is designed to be efficient, accurate, and easy to deploy on standard consumer hardware while still providing powerful natural language understanding capabilities. 