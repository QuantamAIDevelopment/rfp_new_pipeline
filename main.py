from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
from datetime import datetime
import asyncio
from pathlib import Path
import shutil
import tempfile
import pandas as pd
from openpyxl import load_workbook, Workbook
 
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
 
 
@app.get("/download-all-excel/{session_id}")
async def download_all_excel(session_id: str):
    """
    Download all Excel files combined into a single workbook with separate sheets
    """
    base_path = Path("output") / session_id / "excel"
   
    if not base_path.exists():
        raise HTTPException(status_code=404, detail="Excel files not found")
   
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        combined_wb = Workbook()
        combined_wb.remove(combined_wb.active)  # Remove default sheet
       
        excel_files = {
            'boq_excel': 'boq.xlsx',
            'pq_excel': 'prequalification.xlsx',
            'tq_excel': 'technical_qualification.xlsx',
            'summary_excel': 'summary.xlsx',
            'payment_terms_excel': 'payment_terms.xlsx'
        }
       
        for sheet_name, filename in excel_files.items():
            file_path = base_path / filename
            if file_path.exists():
                source_wb = load_workbook(file_path)
                source_ws = source_wb.active
               
                # Create new sheet in combined workbook
                new_ws = combined_wb.create_sheet(title=sheet_name)
               
                # Copy all cells with formatting
                for row in source_ws.iter_rows():
                    for cell in row:
                        new_cell = new_ws.cell(row=cell.row, column=cell.column, value=cell.value)
                        if cell.has_style:
                            new_cell.font = cell.font.copy()
                            new_cell.border = cell.border.copy()
                            new_cell.fill = cell.fill.copy()
                            new_cell.number_format = cell.number_format
                            new_cell.protection = cell.protection.copy()
                            new_cell.alignment = cell.alignment.copy()
               
                # Copy column dimensions
                for col in source_ws.column_dimensions:
                    new_ws.column_dimensions[col] = source_ws.column_dimensions[col]
               
                # Copy row dimensions
                for row in source_ws.row_dimensions:
                    new_ws.row_dimensions[row] = source_ws.row_dimensions[row]
       
        combined_wb.save(tmp_file.name)
       
        return FileResponse(
            path=tmp_file.name,
            filename=f"{session_id}_combined_excel.xlsx",
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
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
async def api_info():
    return {"message": "RFP Processing Pipeline API", "version": "1.0.0"}
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)