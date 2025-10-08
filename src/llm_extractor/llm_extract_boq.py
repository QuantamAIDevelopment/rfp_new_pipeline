import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# Azure OpenAI Configuration
endpoint = "https://allvy-rfp-rg-aai.cognitiveservices.azure.com/"
model_name = "gpt-5-mini"
deployment = "gpt-5-mini"
api_version = "2024-12-01-preview"

def extract_boq_criteria(rfp_content: str, output_path: str):
    """
    Extract Bill of Quantities from RFP content using Azure OpenAI
    """
    
    # Get API key from environment or user input
    subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not subscription_key:
        subscription_key = input("Enter your Azure OpenAI API key: ").strip()
        if not subscription_key:
            print("[ERROR] API key is required")
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
    
    # System prompt for extracting BOQ
    system_prompt = """You are an expert RFP analyst.

Your task is to extract ONLY the **Bill of Quantities (BOQ)** from the given RFP.

### Extraction Rules:
1. Do NOT summarize, paraphrase, or hallucinate. Use EXACT wording from the RFP.
2. Dynamically detect all BOQ-related content, even if it appears in scattered sections:
   - Bill of Quantities
   - Schedule of Items / Price Schedule
   - Material / Equipment / Service Line Items
   - Quantities, Units, Item Descriptions
   - Cost/Rate columns (if provided)
   - Manpower requirements
   - Any annexures or appendices with itemized lists
3. Preserve the **original structure** of the content:
   - If BOQ appears as a table → output as a Markdown table with the **same column headers** as in the RFP.
   - If BOQ appears as bullets or numbered lists → output as Markdown lists.
   - If BOQ appears as plain text → output as paragraphs.
4. Do not reword, rename, or interpret — always keep the **RFP's exact wording**.
5. If a section does not exist → omit it.

### Output Format (STRICTLY FOLLOW):

# Bill of Quantities (Extracted from RFP)

## 1. BOQ Table(s)
[Insert exact BOQ tables from the RFP — preserve original headers and rows exactly]

## 2. BOQ Notes / Instructions
[Insert exact notes, clarifications, or instructions related to BOQ]

---
### Notes:
- Always preserve **original structure and wording**.  
- Do not add explanations or commentary.  
- The only structure that is fixed is the **two main sections above**.
"""

    user_prompt = f"""Please analyze the following RFP content and extract all Bill of Quantities (BOQ) information:

{rfp_content}

Extract and organize all BOQ information into a structured markdown document."""

    try:
        print("[INFO] Analyzing RFP content for Bill of Quantities...")
        
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
        
        print(f"[SUCCESS] Bill of Quantities extracted and saved to {output_path}")
        print(f"[INFO] Extracted content length: {len(extracted_content)} characters")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error extracting Bill of Quantities: {str(e)}")
        return False

def process_rfp_file(input_file: str, output_file: str = None):
    """
    Process an RFP markdown file and extract Bill of Quantities
    """
    if not output_file:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_boq.md"
    
    try:
        # Read the RFP content
        with open(input_file, 'r', encoding='utf-8') as f:
            rfp_content = f.read()
        
        print(f"[INFO] Processing RFP file: {input_file}")
        print(f"[INFO] File size: {len(rfp_content)} characters")
        
        # Extract BOQ
        success = extract_boq_criteria(rfp_content, output_file)
        
        if success:
            print(f"[SUCCESS] Successfully extracted Bill of Quantities to {output_file}")
        
        return success
        
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
    
    # Generate dynamic output filename
    base_name = os.path.splitext(os.path.basename(rfp_file))[0]
    output_file = f"{base_name}_boq.md"
    
    # Process the RFP file
    process_rfp_file(rfp_file, output_file)