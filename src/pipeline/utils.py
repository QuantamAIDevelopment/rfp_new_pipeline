import os
import shutil
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import re

def create_folder_structure(session_id: str, timestamp: str) -> Path:
    """Create organized folder structure for processing session"""
    base_path = Path("output") / session_id
    
    folders = [
        "input",
        "parsed", 
        "extracted",
        "excel"
    ]
    
    for folder in folders:
        (base_path / folder).mkdir(parents=True, exist_ok=True)
    
    return base_path

def cleanup_temp_files(session_folder: Path):
    """Clean up temporary files and folders"""
    if session_folder.exists():
        shutil.rmtree(session_folder)

def convert_markdown_to_excel(markdown_content: str, output_path: Path, sheet_name: str = "Data"):
    """Convert markdown content to Excel format"""
    try:
        # Parse markdown tables if present
        if '|' in markdown_content:
            tables = extract_tables_from_markdown(markdown_content)
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                if tables:
                    for i, table in enumerate(tables):
                        sheet = f"{sheet_name}_{i+1}" if len(tables) > 1 else sheet_name
                        table.to_excel(writer, sheet_name=sheet[:31], index=False)
                else:
                    # Create simple content sheet
                    lines = [line.strip() for line in markdown_content.split('\n') if line.strip()]
                    df = pd.DataFrame({
                        'Line': range(1, len(lines) + 1),
                        'Content': lines
                    })
                    df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        else:
            # Create simple content sheet
            lines = [line.strip() for line in markdown_content.split('\n') if line.strip()]
            df = pd.DataFrame({
                'Line': range(1, len(lines) + 1),
                'Content': lines
            })
            df.to_excel(output_path, sheet_name=sheet_name[:31], index=False)
        
        return True
    except Exception as e:
        print(f"Error converting to Excel: {e}")
        return False

def extract_tables_from_markdown(content: str) -> list:
    """Extract tables from markdown content"""
    tables = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if line contains table separator
        if '|' in line and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            
            # Check if next line is a separator (contains dashes)
            if '|' in next_line and '-' in next_line:
                # Found a table
                headers = [col.strip() for col in line.split('|')[1:-1]]
                
                # Skip separator line
                i += 2
                
                # Collect table rows
                rows = []
                while i < len(lines):
                    row_line = lines[i].strip()
                    if '|' in row_line and row_line:
                        row = [col.strip() for col in row_line.split('|')[1:-1]]
                        if len(row) == len(headers):
                            rows.append(row)
                        i += 1
                    else:
                        break
                
                if rows:
                    df = pd.DataFrame(rows, columns=headers)
                    tables.append(df)
                
                continue
        
        i += 1
    
    return tables

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove extra spaces and dots
    filename = re.sub(r'\s+', '_', filename)
    filename = filename.strip('.')
    return filename[:255]  # Limit length