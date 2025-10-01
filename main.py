from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
from datetime import datetime
import asyncio
from pathlib import Path
import shutil

from pipeline.rfp_processor import RFPProcessor
from pipeline.utils import create_folder_structure, cleanup_temp_files

app = FastAPI(
    title="RFP Processing Pipeline",
    description="Process RFP PDFs through docling and extract structured information",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize the RFP processor (lazy loading)
processor = None

def get_processor():
    global processor
    if processor is None:
        processor = RFPProcessor()
    return processor

@app.post("/process-rfp/")
async def process_rfp(file: UploadFile = File(...)):
    """
    Process an RFP PDF file through the complete pipeline
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Create folder structure for this session
        session_folder = create_folder_structure(session_id, timestamp)
        
        # Save uploaded file
        pdf_path = session_folder / "input" / file.filename
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the RFP through the pipeline
        proc = get_processor()
        result = await proc.process_rfp(pdf_path, session_folder)
        
        return JSONResponse(content={
            "status": "success",
            "session_id": session_id,
            "timestamp": timestamp,
            "message": "RFP processed successfully",
            "files_generated": result["files_generated"],
            "processing_time": result["processing_time"]
        })
        
    except Exception as e:
        # Cleanup on error
        if 'session_folder' in locals():
            cleanup_temp_files(session_folder)
        
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/download/{session_id}/{file_type}")
async def download_file(session_id: str, file_type: str):
    """
    Download processed files by session ID and file type
    """
    base_path = Path("output") / session_id
    
    file_mappings = {
        "markdown": "parsed/rfp.md",
        "boq": "extracted/boq.md",
        "pq": "extracted/prequalification.md", 
        "tq": "extracted/technical_qualification.md",
        "summary": "extracted/summary.md",
        "payment_terms": "extracted/payment_terms.md",
        "boq_excel": "excel/boq.xlsx",
        "pq_excel": "excel/prequalification.xlsx",
        "tq_excel": "excel/technical_qualification.xlsx",
        "summary_excel": "excel/summary.xlsx",
        "payment_terms_excel": "excel/payment_terms.xlsx"
    }
    
    if file_type not in file_mappings:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    file_path = base_path / file_mappings[file_type]
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=f"{session_id}_{file_type}.{file_path.suffix[1:]}",
        media_type='application/octet-stream'
    )

@app.get("/status/{session_id}")
async def get_status(session_id: str):
    """
    Get processing status for a session
    """
    session_folder = Path("output") / session_id
    
    if not session_folder.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check which files exist
    files_status = {}
    file_mappings = {
        "markdown": "parsed/rfp.md",
        "boq": "extracted/boq.md",
        "pq": "extracted/prequalification.md",
        "tq": "extracted/technical_qualification.md", 
        "summary": "extracted/summary.md",
        "payment_terms": "extracted/payment_terms.md"
    }
    
    for file_type, path in file_mappings.items():
        file_path = session_folder / path
        files_status[file_type] = {
            "exists": file_path.exists(),
            "size": file_path.stat().st_size if file_path.exists() else 0
        }
    
    return JSONResponse(content={
        "session_id": session_id,
        "files_status": files_status
    })

@app.delete("/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    """
    Cleanup session files
    """
    session_folder = Path("output") / session_id
    
    if session_folder.exists():
        cleanup_temp_files(session_folder)
        return JSONResponse(content={"message": f"Session {session_id} cleaned up successfully"})
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api")
async def api_info():
    return {"message": "RFP Processing Pipeline API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)