# Academis Quickstart Guide

## Running the Application

### Step 1: Set up the Backend

1. Navigate to the server directory:
   ```
   cd /Users/andywu/Academis/server
   ```

2. Add your OpenAI API key to the `.env` file:
   - Edit the `.env` file and replace `your_openai_api_key_here` with your actual OpenAI API key
   - The MongoDB connection is already configured

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Start the server:
   ```
   python run.py
   ```
   The server will run on http://localhost:8080

### Step 2: Run the Frontend

1. In a new terminal, navigate to the client directory:
   ```
   cd /Users/andywu/Academis/client
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

## Uploading Documents

### Upload Text Files

1. Place your text files in the appropriate directories:
   - AP Microeconomics content: `/Users/andywu/Academis/server/data/micro/`
   - AP Macroeconomics content: `/Users/andywu/Academis/server/data/macro/`

2. Run the document upload script:
   ```
   cd /Users/andywu/Academis/server
   python upload_documents.py
   ```

### Upload PDF Files

To add PDF documents to the knowledge base:

```
cd /Users/andywu/Academis/server
python upload_pdf.py --pdf /path/to/your/document.pdf --subject micro
```

or 

```
python upload_pdf.py --pdf /path/to/your/document.pdf --subject macro
```

## Using the Application

1. Open your browser and go to http://localhost:3000
2. On the home page, select either AP Microeconomics or AP Macroeconomics
3. Use the chat interface to ask questions about the selected subject
4. The system will retrieve relevant information from your uploaded documents and generate responses