import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
import re
import os
 
def create_tq_excel(md_file, excel_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
   
    wb = Workbook()
    ws = wb.active
    ws.title = "Technical Qualification"
   
    # Extract title dynamically
    title_match = re.search(r'^# (.+)', content, re.MULTILINE)
    title = title_match.group(1) if title_match else "Technical Qualification"
   
    # Header
    ws.merge_cells('A1:E1')
    ws['A1'] = title
    ws['A1'].font = Font(bold=True, size=16, color="FFFFFF")
    ws['A1'].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
   
    current_row = 3
   
    # Parse all sections dynamically
    sections = re.findall(r'## (.+?)\n(.*?)(?=##|$)', content, re.DOTALL)
   
    for section_title, section_content in sections:
        # Section header
        ws.merge_cells(f'A{current_row}:E{current_row}')
        ws[f'A{current_row}'] = section_title.upper()
        ws[f'A{current_row}'].font = Font(bold=True, size=14, color="FFFFFF")
        ws[f'A{current_row}'].fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        ws[f'A{current_row}'].alignment = Alignment(horizontal='center')
        current_row += 1
       
        # Check if section contains a table
        table_rows = [row.strip() for row in section_content.split('\n') if '|' in row and row.strip()]
       
        if table_rows:
            # Process table
            header_row = None
            data_rows = []
           
            for row in table_rows:
                if re.match(r'^\|[-\s|]+\|$', row):  # Skip separator rows
                    continue
                cells = [cell.strip() for cell in row.split('|')[1:-1]]  # Remove empty first/last
                if cells:
                    if header_row is None:
                        header_row = cells
                    else:
                        data_rows.append(cells)
           
            # Add table headers
            if header_row:
                for col, header in enumerate(header_row, 1):
                    ws.cell(row=current_row, column=col, value=header)
                    ws.cell(row=current_row, column=col).font = Font(bold=True, color="FFFFFF")
                    ws.cell(row=current_row, column=col).fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                    ws.cell(row=current_row, column=col).alignment = Alignment(horizontal='center', vertical='center')
                current_row += 1
           
            # Add table data
            for row_data in data_rows:
                for col, cell_value in enumerate(row_data, 1):
                    ws.cell(row=current_row, column=col, value=cell_value)
                    ws.cell(row=current_row, column=col).alignment = Alignment(wrap_text=True, vertical='top')
                current_row += 1
        else:
            # Process non-table content
            lines = [line.strip() for line in section_content.split('\n') if line.strip()]
            for line in lines:
                line = re.sub(r'^- ', '', line)  # Remove bullet points
                if line:
                    ws.merge_cells(f'A{current_row}:E{current_row}')
                    ws[f'A{current_row}'] = line
                    ws[f'A{current_row}'].alignment = Alignment(wrap_text=True, vertical='top')
                    current_row += 1
       
        current_row += 1  # Add space between sections
   
    # Set column widths
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['C'].width = 50
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 40
   
    wb.save(excel_file)
    print(f"Excel file created: {excel_file}")
 
if __name__ == "__main__":
    import sys
   
    if len(sys.argv) < 2:
        print("Usage: python pure_tq_to_excel.py <markdown_file> [excel_file]")
        exit(1)
   
    md_file = sys.argv[1]
    excel_file = sys.argv[2] if len(sys.argv) > 2 else md_file.replace('.md', '.xlsx')
   
    if not os.path.exists(md_file):
        print(f"File not found: {md_file}")
        exit(1)
   
    create_tq_excel(md_file, excel_file)