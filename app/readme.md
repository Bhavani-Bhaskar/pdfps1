project-root/
├── main.py                    # Enhanced Flask application with new endpoints
├── validators.py              # PDF validation functions (unchanged)
├── templates/                 # HTML templates for web interface
│   └── index.html            # New drag-and-drop interface
├── static/                   # Static files and CSS/JS
│   ├── css/
│   │   └── style.css        # Styling for drag-and-drop interface
│   └── js/
│       └── dragdrop.js      # JavaScript for drag-and-drop functionality
├── utilities/                # Processing utilities (unchanged)
│   ├── __init__.py
│   ├── image_detector.py
│   ├── metadata_extractor.py
│   ├── pdf_parser.py
│   ├── table_extractor.py
│   └── ocr.py
├── uploads/                  # New folder for uploaded PDFs
├── output/                   # Generated text files
└── requirements.txt          # Dependencies
