// DOM Elements
const fileInput = document.getElementById('pdf-upload');
const uploadStatus = document.getElementById('upload-status');
const documentList = document.getElementById('document-list');
const chatMessages = document.getElementById('chat-messages');
const questionInput = document.getElementById('question-input');
const sendBtn = document.getElementById('send-btn');
const chatForm = document.getElementById('chat-form');
const processingStatus = document.getElementById('processing-status');
const uploadBtn = document.querySelector('.upload-btn');

// Application state
const state = {
  documents: [],
  selectedDocIds: [],
  isLoading: false
};

// Initialize the application
function init() {
  // Add event listeners
  fileInput.addEventListener('change', handleFileUpload);
  chatForm.addEventListener('submit', handleQuestionSubmit);
  
  // Add click handler for the upload button
  uploadBtn.addEventListener('click', () => {
    fileInput.click();
  });
  
  // Load existing documents on startup
  loadDocuments();
}

// Load existing documents from the server
async function loadDocuments() {
  try {
    setLoading(true, 'Loading documents...');
    
    const response = await fetch('/api/documents');
    if (!response.ok) {
      throw new Error('Failed to load documents');
    }
    
    const documents = await response.json();
    
    // Update application state
    state.documents = documents;
    
    // Render documents list
    renderDocumentList();
    
    // Update UI based on document availability
    updateUIState();
    
    setLoading(false);
  } catch (error) {
    console.error('Error loading documents:', error);
    uploadStatus.textContent = `Error: ${error.message}`;
    setLoading(false);
  }
}

// Handle file upload
async function handleFileUpload() {
  console.log('File upload handler triggered');
  
  if (!fileInput.files || fileInput.files.length === 0) {
    console.log('No files selected');
    return;
  }
  
  const file = fileInput.files[0];
  console.log('File selected:', file.name);
  
  // Validate file type
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    uploadStatus.textContent = 'Error: Only PDF files are supported';
    console.log('Invalid file type');
    return;
  }
  
  try {
    setLoading(true, 'Uploading document...');
    uploadStatus.textContent = 'Uploading...';
    
    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    
    // Send file to server
    const response = await fetch('/api/upload-document', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Upload failed');
    }
    
    const result = await response.json();
    
    uploadStatus.textContent = 'Document uploaded successfully!';
    
    // Add new document to state
    state.documents.push({
      id: result.doc_id,
      filename: result.filename
    });
    
    // Select the newly uploaded document
    state.selectedDocIds = [result.doc_id];
    
    // Render updated document list
    renderDocumentList();
    
    // Update UI state
    updateUIState();
    
    // Reset file input
    fileInput.value = '';
    
    setTimeout(() => {
      uploadStatus.textContent = '';
    }, 3000);
    
    setLoading(false);
  } catch (error) {
    console.error('Error uploading document:', error);
    uploadStatus.textContent = `Error: ${error.message}`;
    setLoading(false);
  }
}

// Render document list
function renderDocumentList() {
  // Clear current list
  documentList.innerHTML = '';
  
  // Show empty state if no documents
  if (state.documents.length === 0) {
    const emptyItem = document.createElement('div');
    emptyItem.className = 'doc-item empty-state';
    emptyItem.textContent = 'No documents loaded yet';
    documentList.appendChild(emptyItem);
    return;
  }
  
  // Create document items
  state.documents.forEach(doc => {
    const docItem = document.createElement('div');
    docItem.className = 'doc-item';
    docItem.dataset.docId = doc.id;
    
    // Mark selected documents
    if (state.selectedDocIds.includes(doc.id)) {
      docItem.classList.add('selected');
    }
    
    // Document content
    docItem.innerHTML = `
      <span class="doc-icon">📄</span>
      <span class="doc-name">${doc.filename}</span>
    `;
    
    // Add click handler for selection
    docItem.addEventListener('click', () => {
      toggleDocumentSelection(doc.id);
    });
    
    documentList.appendChild(docItem);
  });
}

// Toggle document selection
function toggleDocumentSelection(docId) {
  const index = state.selectedDocIds.indexOf(docId);
  
  if (index === -1) {
    // Select the document
    state.selectedDocIds.push(docId);
  } else {
    // Deselect the document
    state.selectedDocIds.splice(index, 1);
  }
  
  // Re-render document list
  renderDocumentList();
  
  // Update UI state
  updateUIState();
}

// Update UI state based on application state
function updateUIState() {
  const hasDocuments = state.documents.length > 0;
  const hasSelectedDocs = state.selectedDocIds.length > 0;
  
  // Enable/disable chat input
  questionInput.disabled = !hasSelectedDocs;
  sendBtn.disabled = !hasSelectedDocs;
  
  // Update placeholder text
  if (!hasDocuments) {
    questionInput.placeholder = 'Upload a document first...';
  } else if (!hasSelectedDocs) {
    questionInput.placeholder = 'Select a document to chat with...';
  } else {
    questionInput.placeholder = 'Ask a question about your document...';
  }
}

// Handle question submission
async function handleQuestionSubmit(event) {
  event.preventDefault();
  
  const question = questionInput.value.trim();
  
  // Validate question
  if (!question) {
    return;
  }
  
  try {
    // Add user message to chat
    addMessage(question, 'user');
    
    // Clear input
    questionInput.value = '';
    
    // Show loading indicator
    setLoading(true, 'Thinking...');
    
    // Send question to server
    const response = await fetch('/api/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question,
        doc_ids: state.selectedDocIds
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to get answer');
    }
    
    const result = await response.json();
    
    // Add bot message to chat
    addMessage(result.answer, 'bot', {
      confidence: result.confidence,
      sourceDocument: result.source_document
    });
    
    setLoading(false);
  } catch (error) {
    console.error('Error getting answer:', error);
    addMessage(`Error: ${error.message}`, 'bot');
    setLoading(false);
  }
}

// Add message to chat
function addMessage(text, sender, metadata = {}) {
  const messageElement = document.createElement('div');
  messageElement.className = `message ${sender}-message`;
  
  // Message text
  if (sender === 'bot') {
    // Format bot messages for better readability
    const paragraphs = text.split(/\n+/);
    if (paragraphs.length > 1) {
      // Multiple paragraphs
      paragraphs.forEach(paragraph => {
        if (paragraph.trim()) {
          const p = document.createElement('p');
          p.textContent = paragraph.trim();
          messageElement.appendChild(p);
        }
      });
    } else {
      // Single paragraph
      messageElement.textContent = text;
    }
  } else {
    // User message
    messageElement.textContent = text;
  }
  
  // Add source info for bot messages
  if (sender === 'bot' && metadata.sourceDocument) {
    const sourceInfo = document.createElement('div');
    sourceInfo.className = 'source-info';
    
    const confidence = metadata.confidence ? 
      `${Math.round(metadata.confidence * 100)}% confidence` : '';
    
    sourceInfo.textContent = `Source: ${metadata.sourceDocument} ${confidence}`;
    messageElement.appendChild(sourceInfo);
  }
  
  chatMessages.appendChild(messageElement);
  
  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Set loading state
function setLoading(isLoading, message = '') {
  state.isLoading = isLoading;
  
  if (isLoading) {
    // Show loading indicator
    processingStatus.innerHTML = `
      <div class="loading-indicator">
        <div></div><div></div><div></div><div></div>
      </div>
      ${message}
    `;
    
    // Disable UI
    sendBtn.disabled = true;
    questionInput.disabled = true;
  } else {
    // Hide loading indicator
    processingStatus.innerHTML = '';
    
    // Update UI state
    updateUIState();
  }
}

// Initialize the application
init();