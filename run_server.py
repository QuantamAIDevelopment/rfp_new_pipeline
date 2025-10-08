import uvicorn
import os
from pathlib import Path

def run_server():
    """Run the FastAPI server with proper configuration"""
    
    # Ensure output directory exists
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    print("🚀 Starting RFP Processing Pipeline Server")
    print("=" * 50)
    print("📋 Server Configuration:")
    print(f"   🌐 Host: 127.0.0.1")
    print(f"   🔌 Port: 8000")
    print(f"   📁 Output Directory: {output_dir.absolute()}")
    print(f"   🔄 Auto-reload: True")
    print("=" * 50)
    print("📖 API Endpoints:")
    print("   POST /process-rfp/           - Upload and process RFP PDF")
    print("   GET  /                       - API info")
    print("=" * 50)
    print("🌐 Access the API at: http://localhost:8000")
    print("📚 Interactive docs at: http://localhost:8000/docs")
    print("=" * 50)
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()