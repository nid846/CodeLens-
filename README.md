# CodeLens 🔍

> **Repository-Aware Semantic Source Code Search & Architectural Intelligence Platform**

CodeLens is an intelligent code analysis and discovery platform designed to bridge the **vocabulary mismatch problem** and the **architectural visibility gap** in modern multi-language software repositories. 

It enables engineers to search codebases using natural language intent, visualize cross-file architectural dependencies, and simulate the blast radius of code changes.

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Services** | **Python 3.10+**, **FastAPI**, **Uvicorn**, **Pydantic v2**, **HTTPX** |
| **Code & AST Parsing** | **Tree-sitter** (`tree-sitter-python`, `tree-sitter-java`, `tree-sitter-javascript`, `tree-sitter-typescript`) |
| **AI & Neural Embeddings** | **Jina AI Embeddings v3** (`jina-embeddings-v3`, 1024-dim, task-adapter support) |
| **Vector Database** | **Qdrant Cloud** (HNSW, Cosine similarity, payload keyword indexes) |
| **Information Retrieval** | **Rank-BM25** (BM25Okapi), NumPy |
| **Frontend Application** | **React 19**, **Vite 8**, **@xyflow/react** (React Flow 12), **Dagre**, **Lucide React**, **Oxlint** |
| **Testing & Quality** | **Pytest**, Mock suites, GitHub Actions ready |

---

## Key Features

- **Multi-Language AST Parsing**: Parses Python, Java, JavaScript, TypeScript, and HTML/EJS using Tree-sitter to extract syntactically complete functions, classes, and imports.
- **Interactive Dependency Graph**: Visualizes cross-file imports, class hierarchies, and module relationships using an interactive React Flow (`@xyflow/react`) and Dagre graph layout.
- **Change Impact & Blast Radius (`/api/impact`)**: Performs reverse Breadth-First Search (BFS) graph traversal to identify all downstream files affected when a module is changed.
- **Hybrid Semantic Code Search (`/api/search`)**: Blends BM25 lexical keyword matching with Jina AI neural embeddings (`jina-embeddings-v3`, 1024-dim) in Qdrant Cloud to search code by natural language intent.
- **Token-Efficient Incremental Indexing**: Uses SHA-256 content hashing and vector caching to only re-embed modified code, consuming zero embedding tokens on unchanged files.

---

## 📐 System Architecture

```
                          ┌───────────────────────────────────────┐
                          │   GitHub Repository / Source Code     │
                          └──────────────────┬────────────────────┘
                                             │ git clone
                                             ▼
                          ┌───────────────────────────────────────┐
                          │      Tree-sitter & AST Parsers        │
                          │   (Python, Java, JS/TS, HTML/EJS)     │
                          └──────┬─────────────────────────┬──────┘
                                 │                         │
            ┌────────────────────┴──┐                   ┌──┴────────────────────┐
            ▼                       ▼                   ▼                       ▼
   [ Class & Function Nodes ] [ Imports / Deps ]   [ Syntactic Chunking ]  [ SHA-256 Hashing ]
            │                       │                   │                       │
            └───────────┬───────────┘                   └───────────┬───────────┘
                        ▼                                           ▼
          ┌───────────────────────────┐               ┌───────────────────────────┐
          │ Dependency Knowledge Graph│               │   Incremental Indexing    │
          │  (Directed Graph + BFS)   │               └──────┬─────────────┬──────┘
          └─────────────┬─────────────┘                      │             │
                        │                                    ▼             ▼
                        │                            [BM25 Lexical]   [jina-embeddings-v3]
                        │                             Okapi Engine     (1024-dim passage)
                        │                                    │             │
                        │                                    │             ▼
                        │                                    │      [ Qdrant Cloud ]
                        │                                    │     (Cosine Similarity)
                        ▼                                    ▼             ▼
       ┌──────────────────────────────────────────────────────────────────────────────┐
       │                             FastAPI REST Layer                               │
       │     • POST /api/analyze      • POST /api/search      • POST /api/impact      │
       └──────────────────────────────────────┬───────────────────────────────────────┘
                                              │ HTTP / JSON
                                              ▼
       ┌──────────────────────────────────────────────────────────────────────────────┐
       │                        React 19 + Vite Web Application                       │
       │    • Interactive Dependency Graph (@xyflow/react)    • Hybrid Search Bar     │
       │    • Code Inspector & Syntax Viewer                  • Blast Radius Modal    │
       └──────────────────────────────────────────────────────────────────────────────┘
```

---
## Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**
- **Git** installed on your system
- *(Optional for live semantic vector search)*: Free-tier API keys for [Jina AI](https://jina.ai) and [Qdrant Cloud](https://qdrant.tech). CodeLens will automatically run in lexical BM25 mode if API keys are not provided.

---

### Step 1: Backend Setup (FastAPI)

1. Navigate to the `server` directory:
   ```bash
   cd server
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate    # On Windows: .venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Create a `.env` file in the `server/` directory:
   ```env
   # Jina AI Embeddings Configuration
   JINA_API_KEY=your_jina_api_key_here
   JINA_EMBEDDING_MODEL=jina-embeddings-v3
   JINA_EMBEDDING_DIMENSIONS=1024
   JINA_MONTHLY_TOKEN_BUDGET=1000000

   # Qdrant Vector Database Configuration
   QDRANT_URL=https://your-cluster.qdrant.io:6333
   QDRANT_API_KEY=your_qdrant_api_key_here
   QDRANT_COLLECTION_NAME=codelens_code_chunks

   # Hybrid Search Score Weights
   BM25_WEIGHT=0.5
   SEMANTIC_WEIGHT=0.5
   ```

5. Start the backend development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The API will be available at `http://localhost:8000`. You can inspect the interactive OpenAPI documentation at `http://localhost:8000/docs`.

---

### Step 2: Frontend Setup (React + Vite)

1. In a new terminal, navigate to the `client` directory:
   ```bash
   cd client
   ```

2. Install npm packages:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---