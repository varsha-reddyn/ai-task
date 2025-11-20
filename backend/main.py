from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import os
import uuid
import json
import base64
from PIL import Image
from io import BytesIO
import requests
import tempfile
from dotenv import load_dotenv

load_dotenv()

try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

from database import (
    init_db,
    insert_record,
    get_all_records,
    get_record_by_id,
    get_record_by_task_id,
    update_record,
    delete_record
)

app = FastAPI(title="Handwritten Form Extraction System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "backend/uploads"
RESULTS_DIR = "backend/results"
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-VL-7B-Instruct"

EXTRACTION_PROMPT = """You are an AI expert at reading and extracting information from handwritten forms and documents.

TASK:
Carefully analyze this handwritten form image. Identify all visible fields, labels, and their corresponding handwritten values. Create field names based on what you see in the form.

INSTRUCTIONS:
1. Look for any printed or handwritten labels (like "Name:", "Date:", "Address:", etc.)
2. Extract the handwritten values next to each label
3. If you see fields without clear labels, create appropriate descriptive labels based on the content
4. Include ALL text you can read from the image
5. If text is unclear or illegible, mark the value as "unreadable"

OUTPUT FORMAT (STRICT JSON ONLY):
{
  "fields": [
    {
       "label": "descriptive field name based on what you see",
       "value": "the actual handwritten text you read"
    }
  ]
}

CRITICAL RULES:
- Return ONLY valid JSON, no explanations or additional text
- Create labels dynamically based on what's actually in the image
- Do not assume or invent fields that aren't visible
- Extract exactly what you see, maintain original spelling and formatting
- Be thorough - include all visible text fields"""

class UpdateRecordRequest(BaseModel):
    raw_json: Dict[str, Any]

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Handwritten Form Extraction API", "status": "running"}

def initialize_app():
    """Initialize application on startup."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    init_db()

initialize_app()

def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract text from PDF by converting pages to images and processing each page.
    """
    if not PDF_SUPPORT:
        return {
            "fields": [
                {"label": "PDF Error", "value": "pdf2image library not available"},
                {"label": "Solution", "value": "Install poppler-utils to enable PDF support"}
            ]
        }
    
    try:
        images = convert_from_path(pdf_path, dpi=200)
        
        if not images:
            return {
                "fields": [
                    {"label": "PDF Error", "value": "No pages found in PDF"}
                ]
            }
        
        all_fields = []
        
        for page_num, img in enumerate(images, start=1):
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_image_path = temp_file.name
                img.save(temp_image_path, "JPEG", quality=95)
            
            try:
                page_data = extract_text_from_image(temp_image_path)
                
                if "fields" in page_data:
                    for field in page_data["fields"]:
                        field["label"] = f"Page {page_num} - {field['label']}"
                        all_fields.append(field)
            finally:
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
        
        return {"fields": all_fields if all_fields else [{"label": "No Data", "value": "No text extracted from PDF"}]}
    
    except Exception as e:
        return {
            "fields": [
                {"label": "PDF Processing Error", "value": str(e)},
                {"label": "Error Type", "value": type(e).__name__}
            ]
        }

def extract_text_from_image(image_path: str) -> Dict[str, Any]:
    """
    Extract text from handwritten form using Hugging Face Qwen2-VL model.
    Dynamically creates fields based on what the AI sees in the image.
    """
    # Read API key from environment; prefer `HUGGINGFACE_API_KEY` but allow common alternatives
    hf_token = os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_API_KEY")

    if not hf_token:
        raise ValueError("HUGGINGFACE_API_KEY not found. Please configure your API key in a local .env or environment variable.")
    
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=95)
            img_bytes = buffered.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode()
        
        headers = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.1
        }

        
        api_url = "https://router.huggingface.co/v1/chat/completions"

        response = requests.post(api_url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 503:
            return {
                "fields": [
                    {"label": "Model Status", "value": "Model is loading, please try again in 20-30 seconds"},
                    {"label": "Status Code", "value": "503"}
                ]
            }
        
        if response.status_code != 200:
            error_msg = response.text if response.text else f"HTTP {response.status_code}"
            return {
                "fields": [
                    {"label": "API Error", "value": f"Hugging Face API returned an error"},
                    {"label": "Details", "value": error_msg[:200]},
                    {"label": "Status Code", "value": str(response.status_code)}
                ]
            }
        
        result = response.json()
        
        if isinstance(result, dict) and "choices" in result:
            content = result["choices"][0]["message"]["content"]
            if isinstance(content, list):
                generated_text = " ".join([
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                ])
            else:
                generated_text = content
        elif isinstance(result, list) and len(result) > 0:
            generated_text = result[0].get("generated_text", "")
        elif isinstance(result, dict):
            generated_text = result.get("generated_text", str(result))
        else:
            generated_text = str(result)
        
        try:
            start_idx = generated_text.find('{')
            end_idx = generated_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = generated_text[start_idx:end_idx]
                extracted_data = json.loads(json_str)
                
                if "fields" in extracted_data and isinstance(extracted_data["fields"], list):
                    return extracted_data
                else:
                    return {"fields": [{"label": "Parsing Error", "value": "JSON structure is invalid"}]}
            else:
                return {
                    "fields": [
                        {"label": "Raw AI Response", "value": generated_text[:500]},
                        {"label": "Note", "value": "AI did not return valid JSON. Showing raw response."}
                    ]
                }
        
        except json.JSONDecodeError as e:
            return {
                "fields": [
                    {"label": "JSON Parse Error", "value": str(e)},
                    {"label": "Raw Response", "value": generated_text[:300]}
                ]
            }
    
    except Exception as e:
        return {
            "fields": [
                {"label": "Extraction Error", "value": str(e)},
                {"label": "Error Type", "value": type(e).__name__}
            ]
        }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a handwritten form and extract text using AI.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    allowed_extensions = ['.png', '.jpg', '.jpeg', '.pdf']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    task_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{task_id}{file_ext}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        if file_ext == '.pdf':
            extracted_data = extract_text_from_pdf(file_path)
        else:
            extracted_data = extract_text_from_image(file_path)
        
        result_file_path = os.path.join(RESULTS_DIR, f"{task_id}.json")
        with open(result_file_path, "w") as f:
            json.dump(extracted_data, f, indent=2)
        
        record_id = insert_record(task_id, extracted_data)
        
        return {
            "task_id": task_id,
            "record_id": record_id,
            "status": "success",
            "message": "File uploaded and processed successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    """
    Get extraction result by task ID.
    """
    record = get_record_by_task_id(task_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return {
        "task_id": task_id,
        "record_id": record["id"],
        "data": record["raw_json"],
        "created_at": record["created_at"],
        "updated_at": record["updated_at"]
    }

@app.get("/records")
async def list_records():
    """
    List all extracted records.
    """
    records = get_all_records()
    return {"records": records, "count": len(records)}

@app.get("/records/{record_id}")
async def get_record(record_id: int):
    """
    Get a single record by ID.
    """
    record = get_record_by_id(record_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return record

@app.put("/records/{record_id}")
async def update_record_endpoint(record_id: int, request: UpdateRecordRequest):
    """
    Update an existing record.
    """
    existing_record = get_record_by_id(record_id)
    
    if not existing_record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    success = update_record(record_id, request.raw_json)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update record")
    
    updated_record = get_record_by_id(record_id)
    return updated_record

@app.delete("/records/{record_id}")
async def delete_record_endpoint(record_id: int):
    """
    Delete a record by ID.
    """
    success = delete_record(record_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return {"message": "Record deleted successfully", "record_id": record_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
#
##(venv) PS C:\Users\Aseuro\Downloads\HandwrittenNotes\handwrittennotes\backend> uvicorn main:app --reload --port 8000 or python main.py##npm run dev