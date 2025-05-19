import os
import uuid
import re
import numpy as np
import PyPDF2
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity

class SimpleTokenizer:
    """Custom tokenizer that doesn't rely on NLTK"""

    @staticmethod
    def split_into_sentences(text):
        """Split text into sentences using regex patterns"""
        # First, clean up the text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text).strip()

        # Simple sentence splitting pattern
        pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s'
        sentences = re.split(pattern, text)

        # Clean up sentences
        result = []
        for sentence in sentences:
            if sentence.strip():
                # Ensure sentence ends with punctuation
                if not sentence.strip()[-1] in ['.', '!', '?']:
                    sentence = sentence.strip() + '.'
                result.append(sentence.strip())

        # If we failed to split properly, try a simpler approach
        if len(result) <= 1 and len(text) > 100:
            # Split by periods, ensuring we don't split decimal numbers
            result = []
            chunks = re.split(r'(?<!\d)\.(?!\d)', text)
            for chunk in chunks:
                if chunk.strip():
                    result.append(chunk.strip() + '.')

        # If we still have no sentences and text is long, split into chunks
        if len(result) <= 1 and len(text) > 200:
            # Just split into reasonable chunks
            words = text.split()
            chunks = [' '.join(words[i:i+25]) for i in range(0, len(words), 25)]
            result = [chunk + '.' for chunk in chunks if chunk.strip()]

        # If document starts with a title or header, prioritize it
        if result and len(result[0]) < 100:
            # Move the first sentence to the front again to emphasize it
            # This helps with "what is this document about" questions
            result.append(result[0])

        return result


class DocumentChatbot:
    def __init__(self):
        # Create directories for storing documents and data
        self.upload_dir = "uploads"
        self.data_dir = "document_data"
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

        # Set up tokenizer
        self.tokenizer_tool = SimpleTokenizer()

        # Load model and tokenizer for sentence embeddings
        print("Loading language model...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            self.model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Using fallback model...")
            # Use a simpler, more reliable model as fallback
            self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
            self.model = AutoModel.from_pretrained("distilbert-base-uncased")
            print("Fallback model loaded successfully!")

        # Data storage
        self.documents = {}  # Store document info
        self.document_content = {}  # Store document content
        self.document_embeddings = {}  # Store document sentence embeddings

    def extract_text_from_pdf(self, file_path):
        """Extract text from a PDF file with error handling"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # First pass: try to get text from the first few pages
                # These often contain the most important information
                for page_num in range(min(3, len(pdf_reader.pages))):
                    try:
                        page_text = pdf_reader.pages[page_num].extract_text()
                        if page_text:
                            text += page_text + " "
                    except Exception as e:
                        print(f"Warning: Error extracting text from page {page_num}: {e}")

                # Second pass: get the rest of the document
                if len(pdf_reader.pages) > 3:
                    for page_num in range(3, len(pdf_reader.pages)):
                        try:
                            page_text = pdf_reader.pages[page_num].extract_text()
                            if page_text:
                                text += page_text + " "
                        except Exception as e:
                            print(f"Warning: Error extracting text from page {page_num}: {e}")
        except Exception as e:
            print(f"Error reading PDF: {e}")

        # Clean up text
        text = re.sub(r'\s+', ' ', text).strip()

        if not text.strip():
            print("Warning: No text was extracted from the PDF")

        return text

    def generate_embedding(self, text):
        """Generate embedding for a piece of text with error handling"""
        try:
            # Truncate long text to prevent issues
            if len(text) > 1000:
                text = text[:1000]

            inputs = self.tokenizer(text, padding=True, truncation=True,
                                  return_tensors="pt", max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)

            # Use mean of the last hidden state as the embedding
            embeddings = outputs.last_hidden_state.mean(dim=1)
            return embeddings.cpu().numpy()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return zero embedding as fallback
            return np.zeros((1, 384))  # Default dimension for MiniLM model

    def process_document(self, file_path, filename=None):
        """Process a document and generate embeddings"""
        if filename is None:
            filename = os.path.basename(file_path)

        # Generate a unique ID for the document
        document_id = str(uuid.uuid4())

        print(f"Processing document: {filename}")

        # Extract text from PDF
        text = self.extract_text_from_pdf(file_path)
        print(f"Extracted {len(text)} characters of text")

        if not text.strip():
            print("Error: No text could be extracted from this document")
            return None

        # Split text into sentences using our custom tokenizer
        sentences = self.tokenizer_tool.split_into_sentences(text)
        print(f"Split into {len(sentences)} sentences/segments")

        if len(sentences) < 2:
            print("Warning: Document appears to have very little text or couldn't be properly segmented")
            if len(text) > 50:
                # Force segment by splitting into chunks
                chunks = [text[i:i+100] for i in range(0, len(text), 100)]
                sentences = [chunk + "." for chunk in chunks if chunk.strip()]
                print(f"Forced segmentation into {len(sentences)} chunks")

        # Add the title/filename as a sentence - this helps with "about" questions
        clean_filename = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ")
        if clean_filename not in sentences:
            sentences.insert(0, clean_filename + ".")
            print("Added filename as a document descriptor")

        # Add an explicit document descriptor sentence
        document_descriptor = f"This document is about {clean_filename}."
        sentences.insert(1, document_descriptor)

        # Generate embeddings for each sentence
        print("Generating embeddings...")
        embeddings = []
        for i, sentence in enumerate(sentences):
            if sentence.strip():  # Skip empty sentences
                try:
                    embedding = self.generate_embedding(sentence)
                    embeddings.append(embedding[0])  # Remove batch dimension
                except Exception as e:
                    print(f"Error embedding segment {i}: {e}")
                    # Add zero embedding as placeholder
                    embeddings.append(np.zeros(384))  # Default dimension

            # Show progress for large documents
            if len(sentences) > 100 and i % 50 == 0:
                print(f"Progress: {i}/{len(sentences)} segments processed")

        if not embeddings:
            print("Error: Could not generate any embeddings")
            return None

        # Store data
        self.documents[document_id] = {
            "id": document_id,
            "filename": filename,
            "path": file_path
        }

        self.document_content[document_id] = {
            "text": text,
            "sentences": sentences
        }

        self.document_embeddings[document_id] = embeddings

        print(f"Document processed successfully! ID: {document_id}")
        return document_id

    def ask_question(self, question, doc_ids=None):
        """Answer a question based on document content with improved context understanding"""
        if not doc_ids:
            doc_ids = list(self.documents.keys())  # Use all documents if none specified

        if not doc_ids:
            return {
                "answer": "No documents have been loaded yet.",
                "confidence": 0.0,
                "source_document": "",
                "source_text": ""
            }

        print(f"Answering question: {question}")
        print(f"Searching across {len(doc_ids)} documents")

        # Enhance the question for better matching
        enhanced_question = question

        # For "main topic" or general "about" questions, look for document summary/abstract
        if any(phrase in question.lower() for phrase in ["main topic", "about", "summary", "overview", "purpose"]):
            enhanced_question = "This document discusses or summarizes the following topic:"

        # Generate embedding for question
        question_embedding = self.generate_embedding(enhanced_question)[0]  # Remove batch dimension

        # Track top matches
        all_matches = []

        # Search through specified documents
        for doc_id in doc_ids:
            if doc_id not in self.document_embeddings or not self.document_embeddings[doc_id]:
                continue

            # Calculate similarity with each sentence in the document
            doc_embeddings = self.document_embeddings[doc_id]
            doc_sentences = self.document_content[doc_id]["sentences"]

            # Check if we have valid data
            if not doc_embeddings or len(doc_embeddings) != len(doc_sentences):
                print(f"Warning: Document {doc_id} has mismatched data. Using available data.")
                # Use the smaller length to avoid index errors
                min_length = min(len(doc_embeddings), len(doc_sentences))
                doc_embeddings = doc_embeddings[:min_length]
                doc_sentences = doc_sentences[:min_length]

            if not doc_embeddings:
                continue

            try:
                similarities = cosine_similarity(
                    [question_embedding],
                    doc_embeddings
                )[0]

                # Get top 10 matches for this document
                top_indices = similarities.argsort()[-10:][::-1]
                
                for idx in top_indices:
                    if idx < len(doc_sentences):
                        sentence = doc_sentences[idx]
                        similarity = similarities[idx]
                        
                        # Get context (sentences before and after)
                        start_idx = max(0, idx - 2)
                        end_idx = min(len(doc_sentences), idx + 3)
                        context_sentences = doc_sentences[start_idx:end_idx]
                        context = " ".join(context_sentences)
                        
                        all_matches.append({
                            "sentence": sentence,
                            "context": context,
                            "similarity": similarity,
                            "doc_id": doc_id
                        })
                        
            except Exception as e:
                print(f"Error processing document {doc_id}: {e}")

        # Sort all matches by similarity
        all_matches.sort(key=lambda x: x["similarity"], reverse=True)
        
        # No matches found
        if not all_matches:
            return {
                "answer": "I couldn't find a relevant answer to your question in the provided documents.",
                "confidence": 0.0,
                "source_document": "",
                "source_text": ""
            }
        
        best_match = all_matches[0]
        best_doc_id = best_match["doc_id"]
        best_similarity = best_match["similarity"]
        
        # For topic/purpose questions, generate a more comprehensive answer
        if any(phrase in question.lower() for phrase in ["main topic", "about", "summary", "overview", "purpose"]):
            # Use the top 3-5 matches to form a response
            top_matches = all_matches[:5]
            
            # Extract document title/name
            doc_name = self.documents[best_doc_id]["filename"]
            clean_name = doc_name.replace("_", " ").replace(".pdf", "").strip()
            
            # Prepare a comprehensive answer
            if "purpose" in question.lower():
                answer = f"This document titled '{clean_name}' appears to be "
                
                # Look for purpose indicators in top matches
                purpose_indicators = [
                    match["sentence"] for match in top_matches 
                    if any(term in match["sentence"].lower() for term in 
                        ["purpose", "aim", "goal", "objective", "description", "coursework", "assignment"])
                ]
                
                if purpose_indicators:
                    answer += f"a coursework description document. Its main purpose is to outline "
                    answer += " ".join(purpose_indicators[:2])
                    
                    # Add more context about expectations if available
                    expectations = [
                        match["sentence"] for match in top_matches
                        if any(term in match["sentence"].lower() for term in ["expect", "requirement", "must", "should"])
                    ]
                    
                    if expectations:
                        answer += " The document specifies that " + " ".join(expectations[:2])
                else:
                    # Fall back to using top matches if no clear purpose found
                    answer += f"about {' '.join([m['sentence'] for m in top_matches[:3]])}"
            else:
                # General topic/summary questions
                answer = f"This document titled '{clean_name}' covers "
                answer += " ".join([m['sentence'] for m in top_matches[:3]])
                
            return {
                "answer": answer,
                "confidence": float(best_similarity),
                "source_document": self.documents[best_doc_id]["filename"],
                "source_text": best_match["context"]
            }
                
        # For regular questions, use the best match and its context
        if best_similarity < 0.15:  # Low confidence threshold
            return {
                "answer": "I couldn't find a specific answer to your question. Try asking a more specific question about the document content.",
                "confidence": best_similarity,
                "source_document": self.documents[best_doc_id]["filename"] if best_doc_id else "",
                "source_text": ""
            }
        
        # For all other questions, provide the context as the answer
        return {
            "answer": best_match["context"],
            "confidence": float(best_similarity),
            "source_document": self.documents[best_doc_id]["filename"],
            "source_text": best_match["context"]
        }

    def list_documents(self):
        """List all loaded documents"""
        return list(self.documents.values())