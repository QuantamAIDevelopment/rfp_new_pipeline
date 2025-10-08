import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

endpoint = "https://allvy-rfp-rg-aai.cognitiveservices.azure.com/"
deployment = "gpt-5-mini"
api_version = "2024-12-01-preview"

def extract_pure_technical_qualification(rfp_content: str, output_path: str):
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
    
    system_prompt = """You are an expert RFP analyst.

Extract ONLY the Technical Qualification criteria that are used for SCORING/EVALUATION purposes. 

EXCLUDE:
- Pre-qualification criteria (eligibility requirements)
- General bid submission requirements
- Administrative requirements

INCLUDE ONLY:
- Technical scoring criteria with marks/points
- Technical evaluation parameters with scoring mechanisms
- Technical competence evaluation criteria

Look for sections with:
- "S.No" or "Sr. No."
- "Technical Qualification Criteria" or similar
- "Maximum Score/Marks" or "Points"
- "Scoring Mechanism"
- "Supporting Documents" for technical evaluation

### Output Format:

# Technical Qualification Criteria (Pure Technical Scoring)

## Technical Evaluation Parameters
[Extract the 3 broad parameters with their marks allocation]

## Technical Qualification Scoring Table
[Extract ONLY the technical scoring table with columns like S.No, Technical Qualification Criteria, Maximum Score, Scoring Mechanism, Supporting Documents]

## Technical Evaluation Process
[Extract only the technical evaluation process and scoring methodology]

---
Preserve exact RFP wording and structure."""

    user_prompt = f"""Extract ONLY the technical qualification criteria used for scoring/evaluation from this RFP content. Do NOT include pre-qualification or eligibility criteria:

{rfp_content}"""

    try:
        print("[INFO] Extracting pure technical qualification criteria...")
        
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
        
        print(f"[SUCCESS] Pure technical qualification criteria extracted to {output_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
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
    output_file = f"{base_name}_TQ.md"
    
    # Process the file
    with open(rfp_file, 'r', encoding='utf-8') as f:
        rfp_content = f.read()
    extract_pure_technical_qualification(rfp_content, output_file)