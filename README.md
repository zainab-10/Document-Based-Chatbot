# 📚 Document-Based-Chatbot
## Overview
A web-based chatbot application allows users to upload PDF documents and interact with them via natural language questions. Built with Flask, Transformers, and PyTorch, this chatbot processes and understands your documents, enabling intelligent Q&A functionality.
## Features
- **Document Upload:** Users can upload PDF documents.
- **Document Processing:** Extracts text from PDFs and generates embeddings for each sentence.
- **Question Answering:** Users can ask questions about the uploaded documents, and the chatbot provides relevant answers based on the document content.
- **Document Management:** Lists all uploaded documents and allows users to select specific documents for querying.

## 🧠 How It Works
- **Upload a Document:** Upload a PDF from your local machine.
- **Document Processing:** Text is extracted and broken into sentences.
- **Embedding:** Each sentence is embedded using a pre-trained transformer model.
- **Question Answering:** Input questions are embedded and matched with document content using cosine similarity.
- **Response Generation:** The most relevant sentences are returned as an answer.
- 
## Setup Instructions
### Prerequisites
* Python 3.8 or higher. Ensure you have installed Python 3.8 or higher.
* Docker (optional), Docker is recommended for easy deployment.
* Install dependencies, pip install -r requirements.txt

## Code Structure
- **Flask Application:** app.py handles the web server and API endpoints.
- **Chatbot Logic:** chatbot.py contains the core logic for document processing and question answering.
- **Frontend:** index.html, style.css, and script.js provide the user interface and interaction logic.
-  **NLP Models:** HuggingFace Transformers

## 🧪 Testing
Upload any academic paper, company report, or user manual and ask related questions. The app uses semantic similarity to find the most relevant answers.

## Demo
<video src="document_chatbot.mp4" controls width="600"></video>
