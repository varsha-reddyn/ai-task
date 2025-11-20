# Handwritten Form Extraction System

## Overview
A full-stack web application that uses AI to extract text from handwritten forms. Users can upload images or PDFs, view extracted data in a structured format, and perform CRUD operations on the extracted records.

## Project Architecture

### Backend (Python + FastAPI)
- **Location**: `backend/`
- **Framework**: FastAPI with Uvicorn server
- **Database**: SQLite (file-based database at `backend/database.db`)
- **AI Integration**: Hugging Face Qwen2.5-VL-7B-Instruct model for handwritten text extraction
- **Port**: 8000
- **PDF Support**: Uses pdf2image with poppler to convert PDF pages to images for AI processing

#### API Endpoints
- `POST /upload` - Upload and extract handwritten form
- `GET /result/{task_id}` - Get extraction result by task ID
- `GET /records` - List all extracted records
- `GET /records/{id}` - Get single record by ID
- `PUT /records/{id}` - Update a record
- `DELETE /records/{id}` - Delete a record

#### Database Schema
```
records table:
- id (INTEGER PRIMARY KEY)
- task_id (TEXT UNIQUE)
- raw_json (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

### Frontend (React + Vite)
- **Location**: `frontend/`
- **Framework**: React 18 with Vite build tool
- **Styling**: TailwindCSS
- **Port**: 5000 (proxied to backend on port 8000)

#### Features
1. File upload with drag-and-drop support
2. Upload progress bar
3. Image preview
4. Extracted data display (table view and JSON view)
5. CRUD operations on records
6. Inline editing of extracted fields
7. Download as JSON or CSV
8. Responsive design

## Recent Changes
- **2025-11-19**: Initial project setup
  - Created full-stack application structure
  - Integrated Hugging Face AI model for text extraction
  - Implemented SQLite database with CRUD operations
  - Built React frontend with TailwindCSS
  - Added file upload, preview, and extraction features
  - Implemented record management UI

## Dependencies

### Backend
- fastapi - Web framework
- uvicorn - ASGI server
- python-multipart - File upload handling
- pillow - Image processing
- huggingface-hub - Hugging Face API integration
- requests - HTTP client
- pdf2image - PDF processing

### Frontend
- react - UI framework
- vite - Build tool and dev server
- axios - HTTP client
- react-json-view - JSON viewer component
- tailwindcss - CSS framework

## Environment Variables
- `HUGGINGFACE_API_KEY` (optional) - For real AI extraction. If not set, demo data is used.

## User Preferences
None specified yet.

## Development Notes
- Backend runs on port 8000
- Frontend runs on port 5000 and proxies API requests to backend
- Database is automatically initialized on backend startup
- Uploaded files are stored in `backend/uploads/`
- Extraction results are saved as JSON in `backend/results/`
