#!/usr/bin/env python3
"""
Test script to run Step 2 (LLM Extraction) from existing parsed markdown
"""

import asyncio
import time
from pathlib import Path
import os
import sys

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from llm_extract_boq import extract_boq_criteria
from llm_extract_pq import extract_prequalification_criteria  
from llm_extract_pure_tq import extract_pure_technical_qualification
from rfp_llm_summary import extract_rfp_key_details
from llm_extract_payment_terms import extract_payment_terms

async def test_step2_extraction(session_id: str):
    """Test Step 2 extraction using existing session"""
    
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
    
    # Step 2: Extract information using LLM modules
    print("[INFO] Step 2: Extracting information using LLM modules...")
    start_time = time.time()
    
    # Define extraction tasks
    extraction_tasks = [
        extract_boq_async(rfp_content, extracted_folder),
        extract_pq_async(rfp_content, extracted_folder),
        extract_tq_async(rfp_content, extracted_folder),
        extract_summary_async(rfp_content, extracted_folder),
        extract_payment_terms_async(rfp_content, extracted_folder)
    ]
    
    # Run extractions concurrently
    print("[INFO] Running 5 extraction modules concurrently...")
    extraction_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
    
    # Process results
    successful_extractions = []
    failed_extractions = []
    
    extraction_names = ["BOQ", "Prequalification", "Technical Qualification", "Summary", "Payment Terms"]
    
    for i, result in enumerate(extraction_results):
        if isinstance(result, list) and result:
            successful_extractions.extend(result)
            print(f"[SUCCESS] {extraction_names[i]} extraction completed")
        elif isinstance(result, Exception):
            failed_extractions.append((extraction_names[i], str(result)))
            print(f"[ERROR] {extraction_names[i]} extraction failed: {result}")
        else:
            failed_extractions.append((extraction_names[i], "Unknown error"))
            print(f"[ERROR] {extraction_names[i]} extraction failed")
    
    processing_time = time.time() - start_time
    
    # Summary
    print(f"\n[SUMMARY] Step 2 Extraction Results:")
    print(f"  Processing time: {processing_time:.2f} seconds")
    print(f"  Successful extractions: {len(successful_extractions)}")
    print(f"  Failed extractions: {len(failed_extractions)}")
    
    if successful_extractions:
        print(f"\n[SUCCESS] Generated files:")
        for file_path in successful_extractions:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"  - {file_path} ({file_size} bytes)")
    
    if failed_extractions:
        print(f"\n[ERROR] Failed extractions:")
        for name, error in failed_extractions:
            print(f"  - {name}: {error}")
    
    return len(successful_extractions) > 0

async def extract_boq_async(rfp_content: str, extracted_folder: Path) -> list:
    """Extract Bill of Quantities"""
    def extract_sync():
        output_path = extracted_folder / "boq.md"
        success = extract_boq_criteria(rfp_content, str(output_path))
        return [str(output_path)] if success else []
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, extract_sync)

async def extract_pq_async(rfp_content: str, extracted_folder: Path) -> list:
    """Extract Prequalification criteria"""
    def extract_sync():
        output_path = extracted_folder / "prequalification.md"
        success = extract_prequalification_criteria(rfp_content, str(output_path))
        return [str(output_path)] if success else []
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, extract_sync)

async def extract_tq_async(rfp_content: str, extracted_folder: Path) -> list:
    """Extract Technical Qualification criteria"""
    def extract_sync():
        output_path = extracted_folder / "technical_qualification.md"
        success = extract_pure_technical_qualification(rfp_content, str(output_path))
        return [str(output_path)] if success else []
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, extract_sync)

async def extract_summary_async(rfp_content: str, extracted_folder: Path) -> list:
    """Extract RFP summary"""
    def extract_sync():
        output_path = extracted_folder / "summary.md"
        success = extract_rfp_key_details(rfp_content, str(output_path))
        return [str(output_path)] if success else []
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, extract_sync)

async def extract_payment_terms_async(rfp_content: str, extracted_folder: Path) -> list:
    """Extract Payment Terms"""
    def extract_sync():
        output_path = extracted_folder / "payment_terms.md"
        result = extract_payment_terms(rfp_content, str(output_path))
        return [str(output_path)] if result else []
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, extract_sync)

if __name__ == "__main__":
    # Get session ID from command line or use default
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
    else:
        session_id = "849fadbb-1e54-4db0-abdc-13bb57bd79be"
    
    print(f"[INFO] Testing Step 2 extraction for session: {session_id}")
    print(f"[INFO] Current working directory: {os.getcwd()}")
    
    # Run the test
    success = asyncio.run(test_step2_extraction(session_id))
    
    if success:
        print(f"\n[SUCCESS] Step 2 extraction test completed successfully!")
        print(f"[INFO] Check the extracted files in: output/{session_id}/extracted/")
    else:
        print(f"\n[ERROR] Step 2 extraction test failed!")
    
    exit(0 if success else 1)