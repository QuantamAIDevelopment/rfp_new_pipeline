from docling.document_converter import DocumentConverter

def parse_pdf_to_markdown(pdf_path, output_path):
    """Parse PDF using Docling and save as markdown"""
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    
    # Save as markdown
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result.document.export_to_markdown())
    
    print(f"PDF parsed and saved to: {output_path}")

if __name__ == "__main__":
    pdf_file = r"d:\NEW_DOCLING\RFP2.pdf"
    markdown_file = r"d:\NEW_DOCLING\RFP2.md"
    
    parse_pdf_to_markdown(pdf_file, markdown_file)