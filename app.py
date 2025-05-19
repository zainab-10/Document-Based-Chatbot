# from flask import Flask, render_template, request, jsonify
# import os
# import uuid
# from werkzeug.utils import secure_filename
# from chatbot import DocumentChatbot

# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'uploads'
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# # Ensure upload directory exists
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# # Initialize chatbot
# chatbot = DocumentChatbot()

# @app.route('/')
# def home():
#     return render_template('index.html')

# @app.route('/api/upload-document', methods=['POST'])
# def upload_document():
#     """Handle document upload and processing"""
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file part'}), 400
    
#     file = request.files['file']
    
#     if file.filename == '':
#         return jsonify({'error': 'No selected file'}), 400
    
#     if not file.filename.lower().endswith('.pdf'):
#         return jsonify({'error': 'Only PDF files are supported'}), 400
    
#     try:
#         # Save the file
#         filename = secure_filename(file.filename)
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(file_path)
        
#         # Process the document with chatbot
#         doc_id = chatbot.process_document(file_path, filename)
        
#         if doc_id:
#             return jsonify({
#                 'success': True,
#                 'doc_id': doc_id,
#                 'filename': filename
#             })
#         else:
#             return jsonify({'error': 'Failed to process document'}), 500
            
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/documents', methods=['GET'])
# def list_documents():
#     """Get list of loaded documents"""
#     documents = chatbot.list_documents()
#     return jsonify(documents)

# @app.route('/api/ask', methods=['POST'])
# def ask_question():
#     """Process a question and return answer"""
#     data = request.json
    
#     if not data or 'question' not in data:
#         return jsonify({'error': 'No question provided'}), 400
    
#     question = data['question']
#     doc_ids = data.get('doc_ids', None)  # Optional parameter
    
#     try:
#         answer = chatbot.ask_question(question, doc_ids)
#         return jsonify(answer)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=True)

from flask import Flask, render_template, request, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
from chatbot import DocumentChatbot

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_UPLOAD_SIZE', 16 * 1024 * 1024))  # Default 16MB

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize chatbot
chatbot = DocumentChatbot()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    """Handle document upload and processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
        
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported'}), 400
        
    try:
        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
                
        # Process the document with chatbot
        doc_id = chatbot.process_document(file_path, filename)
                
        if doc_id:
            return jsonify({
                'success': True,
                'doc_id': doc_id,
                'filename': filename
            })
        else:
            return jsonify({'error': 'Failed to process document'}), 500
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def list_documents():
    """Get list of loaded documents"""
    documents = chatbot.list_documents()
    return jsonify(documents)

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Process a question and return answer"""
    data = request.json
        
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400
        
    question = data['question']
    doc_ids = data.get('doc_ids', None)  # Optional parameter
        
    try:
        answer = chatbot.ask_question(question, doc_ids)
        return jsonify(answer)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # In Docker, we should listen on 0.0.0.0
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
