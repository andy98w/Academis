# Academis - Scalable AP Learning Platform

Academis is an AI-powered learning platform designed to help students with Advanced Placement (AP) courses. Currently supporting AP Economics with planned expansion to Biology, Physics, Chemistry, and other AP subjects.

## Project Structure

The project consists of two main parts:

- **Client**: React frontend with TypeScript and Chakra UI
- **Server**: Python backend with FastAPI and LangChain for RAG implementation

## Key Features

- **AI-Powered Tutoring**: Personalized assistance with subject-specific knowledge
- **Interactive Textbooks**: Comprehensive content organized by AP curriculum standards  
- **Practice Assessment**: AP-style questions with instant feedback
- **Scalable Architecture**: Easy expansion to new AP subjects
- **Subject-Specific Chat**: Contextual conversations for each AP subject
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Setup Instructions

### Prerequisites

- Node.js (v16+)
- Python (v3.8+)
- OpenAI API key
- MongoDB Atlas account (for vector storage)

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

4. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   ```

5. Start the server:
   ```
   ./start_server.sh
   ```
   Or manually:
   ```
   python run.py
   ```
   The server will run on http://localhost:8080

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

## Adding Content to the Knowledge Base

### Upload PDF Documents

To add PDF documents to the vector database:

```bash
cd server
python upload_pdf.py --pdf /path/to/your/textbook.pdf
```

The system automatically:
- Extracts text from PDFs using LangChain
- Creates embeddings using OpenAI
- Stores in MongoDB Atlas Vector Search for intelligent retrieval

## API Endpoints

The platform provides scalable REST API endpoints:

### Generic Subject Endpoints
- `POST /api/{subject}/ask` - Ask questions to any subject's AI tutor
- `GET /api/textbook/{subject}/toc` - Get table of contents for any subject
- `GET /api/textbook/{subject}/unit/{unit_id}` - Get specific unit content
- `POST /api/textbook/generate/{subject}` - Generate new textbook content

### Available Subjects
- `micro` - AP Microeconomics
- `macro` - AP Macroeconomics  
- `biology` - AP Biology *(coming soon)*
- `physics` - AP Physics *(coming soon)*
- `chemistry` - AP Chemistry *(coming soon)*

## Architecture Highlights

### Scalable Subject System
- **Backend**: Generic subject handlers with configuration-driven behavior
- **Frontend**: Single reusable components for all subjects
- **Adding New Subjects**: Just 2 configuration entries needed

### Modern Tech Stack
- **FastAPI**: High-performance Python web framework
- **React + TypeScript**: Type-safe frontend development
- **LangChain**: Advanced RAG implementation
- **MongoDB Atlas**: Vector search and document storage
- **Chakra UI**: Responsive, accessible component library

### Performance Features  
- **Intelligent Caching**: Vector embeddings cached for fast retrieval
- **Background Processing**: Textbook generation runs asynchronously
- **Optimized Queries**: Subject-specific search with contextual relevance