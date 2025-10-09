import os
import pandas as pd
from openai import AzureOpenAI
from dotenv import load_dotenv
import json
import re

load_dotenv()

def extract_payment_terms(rfp_content: str, output_path: str):
    """
    Extract payment terms from RFP content using Azure OpenAI
    """
    
    # Get Azure OpenAI configuration from environment variables
    subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://allvy-rfp-rg-aai.cognitiveservices.azure.com/")
    model_name = os.getenv("AZURE_OPENAI_MODEL", "gpt-5-mini")
    deployment = os.getenv("AZURE_OPENAI_MODEL", "gpt-5-mini")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    
    if not subscription_key:
        print("[ERROR] AZURE_OPENAI_API_KEY environment variable is required")
        return False
    
    try:
        # Clear proxy environment variables to avoid conflicts
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        for var in proxy_vars:
            os.environ.pop(var, None)
        
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=subscription_key,
            api_version=api_version
        )
    except Exception as e:
        print(f"Error initializing Azure OpenAI client: {str(e)}")
        return False
    
    # System prompt for extracting payment terms
    system_prompt = """You are an expert RFP analyst.

Your task is to extract ONLY the Payment Terms from the given RFP.

Extraction Rules:
Do NOT summarize, paraphrase, or hallucinate. Use EXACT wording from the RFP.

Dynamically detect all Payment-related content, even if it appears in scattered sections:

Payment Terms / Schedule

Payment Milestones

Advance Payment conditions

Retention Money / Holdback

Penalties / Deductions

Performance Guarantee / Security Deposit linked to payment

Any annexures, clauses, or tables related to payments

Preserve the original structure of the content:

If payment terms appear as a table → output as a Markdown table with the same column headers as in the RFP.

If payment terms appear as bullets or numbered lists → output as Markdown lists.

If payment terms appear as plain text → output as paragraphs.

Do not reword, rename, or interpret — always keep the RFP's exact wording.

If a section does not exist → omit it.

Output Format (STRICTLY FOLLOW):
Payment Terms (Extracted from RFP)
1. Payment Schedule / Milestones
[Insert exact payment milestones from the RFP]

2. Advance Payment
[Insert exact advance payment conditions, if any]

3. Retention / Holdback
[Insert retention money / holdback terms exactly as written]

4. Penalties / Deductions
[Insert penalty conditions related to payment delays, performance issues, etc.]

5. Other Payment-Linked Conditions
[Insert security deposits, performance guarantees, or any other conditions tied to payment]

Notes:
Always preserve original structure and wording.

Do not add explanations or commentary.

The only structure that is fixed is the five main sections above."""

    user_prompt = f"""Please analyze the following RFP content and extract all payment terms:

{rfp_content}

Extract and organize all payment-related information into the structured format specified."""

    try:
        print("[INFO] Analyzing RFP content for payment terms...")
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=16384,
            model=deployment
        )
        
        extracted_content = response.choices[0].message.content
        
        # Save to markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_content)
        
        print(f"[SUCCESS] Payment terms extracted and saved to {output_path}")
        print(f"[INFO] Extracted content length: {len(extracted_content)} characters")
        
        return extracted_content
        
    except Exception as e:
        print(f"[ERROR] Error extracting payment terms: {str(e)}")
        return None

def convert_to_excel(payment_terms_content: str, excel_path: str):
    """
    Convert extracted payment terms to Excel format
    """
    try:
        print("[INFO] Converting payment terms to Excel format...")
        
        # Parse the content and create structured data
        sections = {
            'Payment Schedule / Milestones': [],
            'Advance Payment': [],
            'Retention / Holdback': [],
            'Penalties / Deductions': [],
            'Other Payment-Linked Conditions': []
        }
        
        # Split content by sections
        lines = payment_terms_content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line is a section header
            if any(section in line for section in sections.keys()):
                # Save previous section content
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                for section in sections.keys():
                    if section in line:
                        current_section = section
                        current_content = []
                        break
            else:
                if current_section:
                    current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        # Create Excel workbook with multiple sheets
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            
            # Summary sheet
            summary_data = []
            for section, content in sections.items():
                if content:
                    summary_data.append({
                        'Section': section,
                        'Content': content,
                        'Character Count': len(content)
                    })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Payment Terms Summary', index=False)
            
            # Individual sheets for each section
            for section, content in sections.items():
                if content:
                    # Try to parse tables if present
                    if '|' in content:
                        # Parse markdown table
                        table_lines = [line for line in content.split('\n') if '|' in line]
                        if len(table_lines) >= 2:
                            headers = [col.strip() for col in table_lines[0].split('|')[1:-1]]
                            rows = []
                            for line in table_lines[2:]:  # Skip separator line
                                row = [col.strip() for col in line.split('|')[1:-1]]
                                if len(row) == len(headers):
                                    rows.append(row)
                            
                            if rows:
                                df = pd.DataFrame(rows, columns=headers)
                                sheet_name = section.replace('/', '_')[:31]  # Excel sheet name limit
                                df.to_excel(writer, sheet_name=sheet_name, index=False)
                                continue
                    
                    # Create simple content sheet
                    content_lines = [line for line in content.split('\n') if line.strip()]
                    df = pd.DataFrame({
                        'Line': range(1, len(content_lines) + 1),
                        'Content': content_lines
                    })
                    sheet_name = section.replace('/', '_')[:31]  # Excel sheet name limit
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"[SUCCESS] Payment terms converted to Excel: {excel_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error converting to Excel: {str(e)}")
        return False

def process_rfp_file(input_file: str, output_md: str = None, output_excel: str = None):
    """
    Process an RFP markdown file and extract payment terms
    """
    if not output_md:
        base_name = os.path.splitext(input_file)[0]
        output_md = f"{base_name}_payment_terms.md"
    
    if not output_excel:
        base_name = os.path.splitext(input_file)[0]
        output_excel = f"{base_name}_payment_terms.xlsx"
    
    try:
        # Read the RFP content
        with open(input_file, 'r', encoding='utf-8') as f:
            rfp_content = f.read()
        
        print(f"[INFO] Processing RFP file: {input_file}")
        print(f"[INFO] File size: {len(rfp_content)} characters")
        
        # Extract payment terms
        payment_terms = extract_payment_terms(rfp_content, output_md)
        
        if payment_terms:
            # Convert to Excel
            excel_success = convert_to_excel(payment_terms, output_excel)
            
            if excel_success:
                print(f"[SUCCESS] Successfully processed payment terms:")
                print(f"   [INFO] Markdown: {output_md}")
                print(f"   [INFO] Excel: {output_excel}")
            
            return True
        
        return False
        
    except FileNotFoundError:
        print(f"[ERROR] File not found: {input_file}")
        return False
    except Exception as e:
        print(f"[ERROR] Error processing file: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    # Get input file from command line or user input
    if len(sys.argv) > 1:
        rfp_file = sys.argv[1]
    else:
        rfp_file = input("Enter path to RFP markdown file: ").strip()
    
    if not rfp_file or not os.path.exists(rfp_file):
        print(f"[ERROR] File not found: {rfp_file}")
        exit(1)
    
    # Generate dynamic output filenames
    base_name = os.path.splitext(os.path.basename(rfp_file))[0]
    output_md = f"{base_name}_payment_terms.md"
    output_excel = f"{base_name}_payment_terms.xlsx"
    
    # Process the RFP file
    process_rfp_file(rfp_file, output_md, output_excel)