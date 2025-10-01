import requests
import time
from pathlib import Path

def test_rfp_pipeline():
    """Test the RFP processing pipeline"""
    
    # API base URL
    base_url = "http://localhost:8000"
    
    # Test PDF file path
    pdf_file = Path("RFP2.pdf")
    
    if not pdf_file.exists():
        print("❌ Test PDF file not found. Please ensure RFP2.pdf exists.")
        return
    
    print("🚀 Testing RFP Processing Pipeline")
    print("=" * 50)
    
    # Step 1: Upload and process RFP
    print("📤 Uploading RFP PDF...")
    
    with open(pdf_file, 'rb') as f:
        files = {'file': (pdf_file.name, f, 'application/pdf')}
        response = requests.post(f"{base_url}/process-rfp/", files=files)
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.text}")
        return
    
    result = response.json()
    session_id = result['session_id']
    
    print(f"✅ Upload successful!")
    print(f"📋 Session ID: {session_id}")
    print(f"⏱️ Processing time: {result['processing_time']:.2f} seconds")
    print(f"📁 Files generated: {len(result['files_generated'])}")
    
    # Step 2: Check status
    print("\n🔍 Checking processing status...")
    status_response = requests.get(f"{base_url}/status/{session_id}")
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        print("📊 File Status:")
        for file_type, status in status_data['files_status'].items():
            status_icon = "✅" if status['exists'] else "❌"
            size_info = f"({status['size']} bytes)" if status['exists'] else ""
            print(f"   {status_icon} {file_type}: {size_info}")
    
    # Step 3: Download sample files
    print("\n📥 Testing file downloads...")
    
    download_types = ['markdown', 'boq', 'summary', 'boq_excel']
    
    for file_type in download_types:
        try:
            download_response = requests.get(f"{base_url}/download/{session_id}/{file_type}")
            
            if download_response.status_code == 200:
                # Save downloaded file
                filename = f"test_download_{session_id}_{file_type}"
                if file_type.endswith('_excel'):
                    filename += ".xlsx"
                else:
                    filename += ".md"
                
                with open(filename, 'wb') as f:
                    f.write(download_response.content)
                
                print(f"   ✅ Downloaded {file_type}: {filename}")
            else:
                print(f"   ❌ Failed to download {file_type}: {download_response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Error downloading {file_type}: {e}")
    
    print(f"\n🧹 Cleaning up session...")
    cleanup_response = requests.delete(f"{base_url}/cleanup/{session_id}")
    
    if cleanup_response.status_code == 200:
        print("✅ Session cleaned up successfully")
    else:
        print(f"⚠️ Cleanup warning: {cleanup_response.text}")
    
    print("\n🎉 Pipeline test completed!")

if __name__ == "__main__":
    test_rfp_pipeline()