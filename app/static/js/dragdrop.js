class PDFProcessor {
    constructor() {
        this.dropZone = document.getElementById('drop-zone');
        this.fileInput = document.getElementById('file-input');
        this.browseBtn = document.getElementById('browse-btn');
        this.dropOverlay = document.getElementById('drop-overlay');
        this.uploadProgress = document.getElementById('upload-progress');
        this.progressFill = document.getElementById('progress-fill');
        this.progressText = document.getElementById('progress-text');
        this.statusMessages = document.getElementById('status-messages');
        this.outputList = document.getElementById('output-list');
        this.refreshBtn = document.getElementById('refresh-btn');
        
        this.initializeEventListeners();
        this.loadOutputFiles();
    }
    
    initializeEventListeners() {
        // Drag and drop events
        this.dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
        this.dropZone.addEventListener('dragenter', this.handleDragEnter.bind(this));
        this.dropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.dropZone.addEventListener('drop', this.handleDrop.bind(this));
        
        // Click to browse
        this.browseBtn.addEventListener('click', () => this.fileInput.click());
        this.dropZone.addEventListener('click', () => this.fileInput.click());
        
        // File input change
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        
        // Refresh button
        this.refreshBtn.addEventListener('click', this.loadOutputFiles.bind(this));
        
        // Prevent default drag behaviors on document
        document.addEventListener('dragover', (e) => e.preventDefault());
        document.addEventListener('drop', (e) => e.preventDefault());
    }
    
    handleDragOver(e) {
        e.preventDefault();
        this.dropZone.classList.add('drag-over');
        this.dropOverlay.classList.add('active');
    }
    
    handleDragEnter(e) {
        e.preventDefault();
        this.dropZone.classList.add('drag-over');
        this.dropOverlay.classList.add('active');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        if (!this.dropZone.contains(e.relatedTarget)) {
            this.dropZone.classList.remove('drag-over');
            this.dropOverlay.classList.remove('active');
        }
    }
    
    handleDrop(e) {
        e.preventDefault();
        this.dropZone.classList.remove('drag-over');
        this.dropOverlay.classList.remove('active');
        
        const files = Array.from(e.dataTransfer.files);
        this.processFiles(files);
    }
    
    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.processFiles(files);
    }
    
    processFiles(files) {
        const pdfFiles = files.filter(file => file.type === 'application/pdf');
        
        if (pdfFiles.length === 0) {
            this.showMessage('Please select PDF files only.', 'error');
            return;
        }
        
        if (pdfFiles.length !== files.length) {
            this.showMessage('Some files were skipped. Only PDF files are supported.', 'info');
        }
        
        // Process each PDF file
        pdfFiles.forEach(file => this.uploadFile(file));
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            this.showUploadProgress(true);
            this.updateProgress(0, `Uploading ${file.name}...`);
            
            const response = await fetch('/store', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.updateProgress(100, 'Processing complete!');
                this.showMessage(
                    `Successfully processed: ${result.original_filename}`, 
                    'success'
                );
                
                // Refresh output list
                setTimeout(() => {
                    this.loadOutputFiles();
                    this.showUploadProgress(false);
                }, 2000);
            } else {
                throw new Error(result.error || 'Upload failed');
            }
            
        } catch (error) {
            this.showUploadProgress(false);
            this.showMessage(`Error processing ${file.name}: ${error.message}`, 'error');
        }
    }
    
    showUploadProgress(show) {
        this.uploadProgress.style.display = show ? 'block' : 'none';
        if (!show) {
            this.progressFill.style.width = '0%';
        }
    }
    
    updateProgress(percent, text) {
        this.progressFill.style.width = `${percent}%`;
        this.progressText.textContent = text;
    }
    
    showMessage(message, type) {
        const messageElement = document.createElement('div');
        messageElement.className = `status-message ${type}`;
        messageElement.textContent = message;
        
        this.statusMessages.appendChild(messageElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 5000);
    }
    
    async loadOutputFiles() {
        try {
            this.outputList.innerHTML = '<p class="loading">Loading processed files...</p>';
            
            const response = await fetch('/output');
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.displayOutputFiles(result.files);
            } else {
                throw new Error(result.error || 'Failed to load files');
            }
            
        } catch (error) {
            this.outputList.innerHTML = `<p class="loading error">Error loading files: ${error.message}</p>`;
        }
    }
    
    displayOutputFiles(files) {
        if (files.length === 0) {
            this.outputList.innerHTML = '<p class="loading">No processed files found.</p>';
            return;
        }
        
        this.outputList.innerHTML = files.map(file => `
            <div class="output-item">
                <h3>${file.filename}</h3>
                <div class="meta">
                    <div>Size: ${this.formatFileSize(file.size)}</div>
                    <div>Created: ${this.formatDate(file.created)}</div>
                </div>
                <div class="actions">
                    <button class="download-btn" onclick="window.open('/output/${encodeURIComponent(file.filename)}', '_blank')">
                        Download
                    </button>
                    <button class="view-btn" onclick="pdfProcessor.viewFile('${file.filename}')">
                        View
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    async viewFile(filename) {
        try {
            const response = await fetch(`/output/${encodeURIComponent(filename)}/view`);
            const result = await response.json();
            
            if (response.ok && result.success) {
                const newWindow = window.open('', '_blank');
                newWindow.document.write(`
                    <html>
                        <head>
                            <title>${filename}</title>
                            <style>
                                body { font-family: monospace; padding: 20px; white-space: pre-wrap; }
                                .header { font-family: sans-serif; border-bottom: 1px solid #ccc; padding-bottom: 10px; margin-bottom: 20px; }
                            </style>
                        </head>
                        <body>
                            <div class="header">
                                <h2>${filename}</h2>
                                <p>Content Length: ${result.content_length} characters</p>
                            </div>
                            ${result.content}
                        </body>
                    </html>
                `);
                newWindow.document.close();
            } else {
                throw new Error(result.error || 'Failed to view file');
            }
            
        } catch (error) {
            this.showMessage(`Error viewing file: ${error.message}`, 'error');
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
}

// Initialize the PDF processor when the page loads
let pdfProcessor;
document.addEventListener('DOMContentLoaded', () => {
    pdfProcessor = new PDFProcessor();
});
