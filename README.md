# Agentic RAG System

A modular Retrieval-Augmented Generation (RAG) system coupled with an Agentic Demand Calculator. This project is designed with a 3-layer architecture (`directives`, `app`, `tools`) to support multi-faceted AI interactions, specifically tailored for Electrical Code compliance, Healthcare facility planning, and Military standards.

## 🏗️ Architecture

The codebase is organized into three distinct layers:

1.  **Directives (`directives/`)**:
    *   Contains the "Brain" of the project.
    *   Stores high-level architecture documents, feature specifications, and agent protocols.
    *   Key file: `RAG_Architecture_V3.md`.

2.  **Application (`app/`)**:
    *   **`rag_core/`**: The heart of the RAG system. Includes `rag_agent.py` (logic), `rag_chat.py` (interface), and `rag_engine.py` (retrieval).
    *   **`interface/`**: User-facing components.
        *   `demand_calculator/`: A robust electrical load calculation engine supporting NEC standards (Elevators, HVAC, Data Centers, etc.).

3.  **Tools (`tools/`)**:
    *   **`admin/`**: Maintenance scripts (e.g., `ingest_books.py` for indexing documents).
    *   **`tests/`**: Verification scripts to ensure system integrity.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [ChromaDB](https://docs.trychroma.com/) (Local vector store)
- OpenAI API Key

### Installation

1.  **Clone the repository**:
    ```bash
    git clone git@github.com:ysokayev/rag-ai.git
    cd rag-ai
    ```

2.  **Set up Virtual Environment**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate   # Windows
    # source venv/bin/activate # Mac/Linux
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variables**:
    Create a `.env` file in the root directory:
    ```env
    OPENAI_API_KEY=sk-your-key-here
    ```

## 🛠️ Usage

### 1. Running the RAG Chat
Start the interactive chat session to query your document knowledge base:
```bash
python app/rag_core/rag_chat.py
```

### 2. Using the Demand Calculator
The calculator is integrated into the RAG Agent but can also be tested independently:
```bash
# Run the comprehensive test suite
python app/interface/demand_calculator/test_comprehensive.py
```

### 3. Ingesting New Documents
To add new books or code standards to the Vector Database:
```bash
# Ingest Healthcare documents
python tools/admin/ingest_books.py --domain healthcare

# Ingest generic Code Books
python tools/admin/ingest_books.py --domain code
```

## 🧪 Testing

Run the verification scripts to ensure the environment is correctly set up:
```bash
python tools/tests/verify_rag.py   # Test RAG Core
python tools/tests/verify_calc.py  # Test Logic Tools
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
