import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# Azure OpenAI Configuration
endpoint = "https://allvy-rfp-rg-aai.cognitiveservices.azure.com/"
model_name = "gpt-5-mini"
deployment = "gpt-5-mini"
api_version = "2024-12-01-preview"

def extract_rfp_key_details(rfp_content: str, output_path: str):
    """
    Extract key RFP details and create a structured summary
    """
    
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
    
    system_prompt = """You are an expert RFP analyst specializing in extracting key details from RFP documents.

Your task is to extract and summarize the RFP according to the specified key details format.

### Required Key Details to Extract:
1. Project Name
2. Document Title  
3. Client Name
4. Purpose of RFP
5. Contact Information
6. RFP Advertising Date
7. Website for Document Download
8. RFP Document Fee
9. Earnest Money Deposit (EMD)
10. EMD Submission Due Date & Time
11. Last Date for Written Queries
12. Pre-Bid Meeting Date & Time
13. Pre-Bid Meeting Venue
14. Last Date & Time for Bid Submission
15. Technical Bid Opening Date & Time
16. Financial Bid Opening
17. Bid Submission Process
18. Project Duration
19. Evaluation Method
20. Scope of work

### Instructions:
1. Extract EXACT information from the RFP - do not paraphrase or interpret
2. If any key detail is not found, mark it as "Not specified in RFP"
3. If you find additional important key details not in the above list, add them as "Additional Key Details"
4. Keep summaries brief and factual
5. Use bullet points for complex information

### Output Format:

# RFP Key Details Summary

**Project Title:** [Extract exact project name/title]

## Core RFP Information

| Key Detail | Information |
|------------|-------------|
| Project Name | [Extract exact name] |
| Document Title | [Extract exact title] |
| Client Name | [Extract client/organization name] |
| Purpose of RFP | [Brief purpose statement] |
| Contact Information | [Contact details] |
| RFP Advertising Date | [Date if mentioned] |
| Website for Document Download | [URL if mentioned] |
| RFP Document Fee | [Fee amount if mentioned] |
| Earnest Money Deposit (EMD) | [EMD amount] |
| EMD Submission Due Date & Time | [Date and time] |
| Last Date for Written Queries | [Date] |
| Pre-Bid Meeting Date & Time | [Date and time] |
| Pre-Bid Meeting Venue | [Venue details] |
| Last Date & Time for Bid Submission | [Date and time] |
| Technical Bid Opening Date & Time | [Date and time] |
| Financial Bid Opening | [Date and time] |
| Bid Submission Process | [Brief process description] |
| Project Duration | [Duration/timeline] |
| Evaluation Method | [Evaluation criteria/method] |

## Scope of Work
[Brief summary of main scope items]

## Additional Key Details
[Any other important details found in the RFP that weren't in the original list]

---
**Note:** Information extracted directly from RFP document. Details marked as "Not specified in RFP" were not found in the source document."""

    user_prompt = f"""Please analyze the following RFP content and extract all key details according to the specified format:

{rfp_content}

Create a comprehensive summary of the RFP key details."""

    try:
        print("[INFO] Extracting RFP key details...")
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=16384,
            model=deployment
        )
        
        extracted_content = response.choices[0].message.content
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_content)
        
        print(f"[SUCCESS] RFP key details extracted and saved to {output_path}")
        print(f"[INFO] Extracted content length: {len(extracted_content)} characters")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error extracting RFP key details: {str(e)}")
        return False

def process_rfp_file(input_file: str, output_file: str = None):
    """
    Process an RFP markdown file and extract key details
    """
    if not output_file:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_key_details.md"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            rfp_content = f.read()
        
        print(f"[INFO] Processing RFP file: {input_file}")
        print(f"[INFO] File size: {len(rfp_content)} characters")
        
        success = extract_rfp_key_details(rfp_content, output_file)
        
        if success:
            print(f"[SUCCESS] Successfully extracted RFP key details to {output_file}")
        
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
    output_file = f"{base_name}_summary.md"
    
    # Process the RFP file
    process_rfp_file(rfp_file, output_file)