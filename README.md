# Academis - AP Economics Assistant

Academis is an AI-powered application designed to help students with AP Economics courses, specifically Microeconomics and Macroeconomics.

## Project Structure

The project consists of two main parts:

- **Client**: React frontend with TypeScript
- **Server**: Python backend with FastAPI and LangChain for RAG implementation

## Setup Instructions

### Prerequisites

- Node.js (v14+)
- Python (v3.8+)
- OpenAI API key

### Backend Setup

1. Navigate to the server directory:
   ```
   cd server
   ```

2. Create a Python virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure your OpenAI API key in the `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. Start the server:
   ```
   python run.py
   ```
   The server will run on http://localhost:5000

### Frontend Setup

1. Navigate to the client directory:
   ```
   cd client
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```
   The frontend will run on http://localhost:3000

## Adding Content for RAG

### Text Files
To add text content for the Retrieval-Augmented Generation system:

1. Place text files with AP Microeconomics content in `server/data/micro/`
2. Place text files with AP Macroeconomics content in `server/data/macro/`
3. Run the upload script to ingest the files:

```
python upload_documents.py
```

### PDF Files
To add PDF documents to the knowledge base:

1. Use the upload_pdf.py script to add a PDF to the MongoDB vector store:

```
python upload_pdf.py --pdf /path/to/your/document.pdf --subject micro
```

or

```
python upload_pdf.py --pdf /path/to/your/document.pdf --subject macro
```

The system stores documents in MongoDB Atlas Vector Search and retrieves relevant context when answering student questions.

## Features

- Interactive chat interface for asking questions about AP Economics
- Separate sections for Microeconomics and Macroeconomics
- RAG-based answers that leverage both curated content and large language models