#!/usr/bin/env python3
"""
Test script to run Step 3 (Excel Conversion) from existing extracted markdown files
"""

import asyncio
import time
from pathlib import Path
import os
import sys
import pandas as pd

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def convert_markdown_to_excel_simple(markdown_path: Path, excel_path: Path, sheet_name: str = "Data"):
    """Simple markdown to Excel converter"""
    try:
        # Create excel directory if it doesn't exist
        excel_path.parent.mkdir(exist_ok=True)
        
        # Read markdown content
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into lines
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Try to detect tables
        tables = []
        current_table = []
        in_table = False
        
        for line in lines:
            if '|' in line and not line.startswith('#'):
                if not in_table:
                    in_table = True
                    current_table = []
                current_table.append(line)
            else:
                if in_table and current_table:
                    tables.append(current_table)
                    current_table = []
                    in_table = False
        
        # Add last table if exists
        if current_table:
            tables.append(current_table)
        
        # Create Excel workbook
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            
            # If tables found, create separate sheets for each
            if tables:
                for i, table in enumerate(tables):
                    if len(table) >= 2:  # At least header and one row
                        # Parse table
                        headers = [col.strip() for col in table[0].split('|')[1:-1]]
                        rows = []
                        
                        for row_line in table[2:]:  # Skip separator line
                            if '|' in row_line:
                                row = [col.strip() for col in row_line.split('|')[1:-1]]
                                if len(row) == len(headers):
                                    rows.append(row)
                        
                        if rows:
                            df = pd.DataFrame(rows, columns=headers)
                            sheet_name_table = f"Table_{i+1}" if len(tables) > 1 else sheet_name
                            df.to_excel(writer, sheet_name=sheet_name_table[:31], index=False)
            
            # Create a summary sheet with all content
            content_lines = []
            section = ""
            
            for line in lines:
                if line.startswith('#'):
                    section = line.replace('#', '').strip()
                elif line and not line.startswith('|'):
                    content_lines.append({
                        'Section': section,
                        'Content': line,
                        'Length': len(line)
                    })
            
            if content_lines:
                summary_df = pd.DataFrame(content_lines)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            else:
                # Fallback: create simple text sheet
                simple_df = pd.DataFrame({
                    'Line': range(1, len(lines) + 1),
                    'Content': lines
                })
                simple_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Excel conversion failed for {markdown_path}: {e}")
        return False

async def convert_to_excel_async(markdown_path: Path, excel_path: Path, converter_type: str) -> str:
    """Convert markdown to Excel asynchronously"""
    def convert_sync():
        if not markdown_path.exists():
            print(f"[WARNING] Markdown file not found: {markdown_path}")
            return None
        
        try:
            success = convert_markdown_to_excel_simple(markdown_path, excel_path, converter_type.upper())
            if success:
                print(f"[SUCCESS] {converter_type.upper()} converted to Excel: {excel_path}")
                return str(excel_path)
            else:
                print(f"[ERROR] Failed to convert {converter_type}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Excel conversion error for {converter_type}: {e}")
            return None
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, convert_sync)

async def test_step3_excel_conversion(session_id: str):
    """Test Step 3 Excel conversion using existing extracted files"""
    
    # Define paths
    base_path = Path("output") / session_id
    extracted_folder = base_path / "extracted"
    excel_folder = base_path / "excel"
    
    # Create excel folder if it doesn't exist
    excel_folder.mkdir(exist_ok=True)
    
    # Check if extracted folder exists
    if not extracted_folder.exists():
        print(f"[ERROR] Extracted folder not found: {extracted_folder}")
        return False
    
    print(f"[INFO] Step 3: Converting extracted files to Excel format...")
    start_time = time.time()
    
    # Define conversion tasks
    conversion_tasks = [
        convert_to_excel_async(
            extracted_folder / "boq.md",
            excel_folder / "boq.xlsx",
            "BOQ"
        ),
        convert_to_excel_async(
            extracted_folder / "prequalification.md",
            excel_folder / "prequalification.xlsx",
            "Prequalification"
        ),
        convert_to_excel_async(
            extracted_folder / "technical_qualification.md",
            excel_folder / "technical_qualification.xlsx",
            "Technical_Qualification"
        ),
        convert_to_excel_async(
            extracted_folder / "summary.md",
            excel_folder / "summary.xlsx",
            "Summary"
        ),
        convert_to_excel_async(
            extracted_folder / "payment_terms.md",
            excel_folder / "payment_terms.xlsx",
            "Payment_Terms"
        )
    ]
    
    # Run conversions concurrently
    print("[INFO] Running 5 Excel conversions concurrently...")
    conversion_results = await asyncio.gather(*conversion_tasks, return_exceptions=True)
    
    # Process results
    successful_conversions = []
    failed_conversions = []
    
    conversion_names = ["BOQ", "Prequalification", "Technical Qualification", "Summary", "Payment Terms"]
    
    for i, result in enumerate(conversion_results):
        if isinstance(result, str) and result:
            successful_conversions.append(result)
            print(f"[SUCCESS] {conversion_names[i]} Excel conversion completed")
        elif isinstance(result, Exception):
            failed_conversions.append((conversion_names[i], str(result)))
            print(f"[ERROR] {conversion_names[i]} Excel conversion failed: {result}")
        else:
            failed_conversions.append((conversion_names[i], "Conversion returned None"))
            print(f"[WARNING] {conversion_names[i]} Excel conversion skipped")
    
    processing_time = time.time() - start_time
    
    # Summary
    print(f"\n[SUMMARY] Step 3 Excel Conversion Results:")
    print(f"  Processing time: {processing_time:.2f} seconds")
    print(f"  Successful conversions: {len(successful_conversions)}")
    print(f"  Failed conversions: {len(failed_conversions)}")
    
    if successful_conversions:
        print(f"\n[SUCCESS] Generated Excel files:")
        for file_path in successful_conversions:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"  - {file_path} ({file_size} bytes)")
    
    if failed_conversions:
        print(f"\n[ERROR] Failed conversions:")
        for name, error in failed_conversions:
            print(f"  - {name}: {error}")
    
    return len(successful_conversions) > 0

if __name__ == "__main__":
    # Use the existing session ID
    session_id = "849fadbb-1e54-4db0-abdc-13bb57bd79be"
    
    print(f"[INFO] Testing Step 3 Excel conversion for session: {session_id}")
    print(f"[INFO] Current working directory: {os.getcwd()}")
    
    # Run the test
    success = asyncio.run(test_step3_excel_conversion(session_id))
    
    if success:
        print(f"\n[SUCCESS] Step 3 Excel conversion test completed successfully!")
        print(f"[INFO] Check the Excel files in: output/{session_id}/excel/")
    else:
        print(f"\n[ERROR] Step 3 Excel conversion test failed!")
    
    exit(0 if success else 1)