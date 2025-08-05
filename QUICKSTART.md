# Academis Quickstart Guide

## Running the Application

### Step 1: Set up the Backend

1. Navigate to the server directory:
   ```
   cd server
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   MONGODB_URI=your_mongodb_connection_string
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

### Step 2: Run the Frontend

1. In a new terminal, navigate to the client directory:
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

### Upload PDF Files

To add PDF documents to the vector database:

```bash
cd server
python upload_pdf.py --pdf /path/to/your/document.pdf
```

The script will automatically detect and store the content in MongoDB Atlas Vector Search for retrieval.

## Using the Application

1. Open your browser and go to http://localhost:3000
2. Choose from available AP subjects:
   - **AP Microeconomics** - Individual economic behavior and markets
   - **AP Macroeconomics** - National economies and government policies  
   - **AP Biology** - Life sciences and cellular processes *(coming soon)*
   - **AP Physics** - Mechanics and modern physics *(coming soon)*
   - **AP Chemistry** - Chemical bonding and reactions *(coming soon)*

3. On any subject page:
   - **Interactive Textbook**: Browse organized content by units and chapters
   - **AI Tutor**: Ask questions using the chat interface
   - **Practice Questions**: Test knowledge with AP-style questions

4. The AI tutor retrieves relevant information from the knowledge base and provides personalized responses

## Adding New AP Subjects

The platform is designed to easily support new AP subjects:

1. **Backend**: Add subject configuration to `server/app/subject_config.py`
2. **Frontend**: Add subject details to `client/src/config/subjects.ts`  
3. **Content**: Upload subject-specific PDFs using the upload script

That's it! The system automatically handles routing, theming, and functionality for the new subject.