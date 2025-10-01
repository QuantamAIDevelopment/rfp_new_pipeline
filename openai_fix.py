"""
OpenAI client fix for proxy parameter error
"""
import os
from openai import AzureOpenAI

def create_azure_openai_client(endpoint, api_key, api_version):
    """
    Create AzureOpenAI client with proper error handling for proxy parameters
    """
    # Clear all proxy-related environment variables
    proxy_vars = [
        'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
        'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy',
        'EXPERIMENTAL_HTTP_PROXY_SUPPORT'
    ]
    
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]
    
    try:
        # Try standard initialization
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        return client
    except TypeError as e:
        if 'proxies' in str(e):
            # If proxies error, try with minimal parameters
            try:
                client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=api_key,
                    api_version=api_version,
                    timeout=60.0
                )
                return client
            except Exception:
                # Last resort - basic initialization
                client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=api_key,
                    api_version=api_version
                )
                return client
        else:
            raise e