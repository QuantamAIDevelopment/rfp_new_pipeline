#!/usr/bin/env python3
"""
Test single extraction to debug the proxy error
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from llm_extract_boq import extract_boq_criteria

def test_single_extraction():
    """Test single BOQ extraction"""
    
    session_id = "849fadbb-1e54-4db0-abdc-13bb57bd79be"
    
    # Define paths
    base_path = Path("output") / session_id
    markdown_path = base_path / "parsed" / "rfp.md"
    extracted_folder = base_path / "extracted"
    
    # Create extracted folder if it doesn't exist
    extracted_folder.mkdir(exist_ok=True)
    
    # Check if markdown file exists
    if not markdown_path.exists():
        print(f"[ERROR] Markdown file not found: {markdown_path}")
        return False
    
    # Read the parsed markdown content
    print(f"[INFO] Reading markdown file: {markdown_path}")
    with open(markdown_path, 'r', encoding='utf-8') as f:
        rfp_content = f.read()
    
    print(f"[INFO] Markdown file size: {len(rfp_content)} characters")
    
    # Test BOQ extraction
    print("[INFO] Testing BOQ extraction...")
    output_path = extracted_folder / "boq.md"
    
    try:
        success = extract_boq_criteria(rfp_content, str(output_path))
        if success:
            print(f"[SUCCESS] BOQ extraction completed: {output_path}")
            return True
        else:
            print("[ERROR] BOQ extraction failed")
            return False
    except Exception as e:
        print(f"[ERROR] BOQ extraction exception: {e}")
        return False

if __name__ == "__main__":
    print("[INFO] Testing single BOQ extraction...")
    success = test_single_extraction()
    
    if success:
        print("[SUCCESS] Single extraction test passed!")
    else:
        print("[ERROR] Single extraction test failed!")
    
    exit(0 if success else 1)