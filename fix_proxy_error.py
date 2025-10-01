#!/usr/bin/env python3
"""
Fix proxy error by updating all extraction modules
"""

import os
import re
from pathlib import Path

def fix_extraction_module(file_path):
    """Fix a single extraction module"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the AzureOpenAI initialization
    old_pattern = r'client = AzureOpenAI\(\s*api_version=api_version,\s*azure_endpoint=endpoint,\s*api_key=subscription_key\s*\)'
    
    new_initialization = '''# Clear proxy environment variables to avoid conflicts
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        for var in proxy_vars:
            os.environ.pop(var, None)
        
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=subscription_key,
            api_version=api_version
        )'''
    
    # Replace the initialization
    content = re.sub(old_pattern, new_initialization, content)
    
    # Also handle the alternative pattern
    alt_pattern = r'client = AzureOpenAI\(\s*azure_endpoint=endpoint,\s*api_key=subscription_key,\s*api_version=api_version\s*\)'
    content = re.sub(alt_pattern, new_initialization, content)
    
    # Write back the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[SUCCESS] Fixed {file_path}")

def main():
    """Fix all extraction modules"""
    
    extraction_files = [
        "llm_extract_boq.py",
        "llm_extract_pq.py", 
        "llm_extract_pure_tq.py",
        "llm_extract_payment_terms.py",
        "rfp_llm_summary.py"
    ]
    
    print("[INFO] Fixing proxy errors in extraction modules...")
    
    for file_name in extraction_files:
        file_path = Path(file_name)
        if file_path.exists():
            fix_extraction_module(file_path)
        else:
            print(f"[WARNING] File not found: {file_path}")
    
    print("[SUCCESS] All extraction modules have been fixed!")
    print("[INFO] The proxy parameter error should now be resolved.")

if __name__ == "__main__":
    main()