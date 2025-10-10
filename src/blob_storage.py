from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import os
from datetime import datetime

class BlobStorage:
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        
        if self.connection_string:
            self.blob_client = BlobServiceClient.from_connection_string(self.connection_string)
        else:
            credential = DefaultAzureCredential()
            self.blob_client = BlobServiceClient(
                account_url=f"https://{self.account_name}.blob.core.windows.net",
                credential=credential
            )
        
        self.container_name = "rfp-results"
        self._ensure_container()
    
    def _ensure_container(self):
        try:
            self.blob_client.create_container(self.container_name)
        except:
            pass
    
    def upload_file(self, file_path: str, original_filename: str):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = original_filename.replace('.pdf', '')
        blob_name = f"{base_name}_{timestamp}.xlsx"
        
        with open(file_path, "rb") as data:
            self.blob_client.get_blob_client(
                container=self.container_name, 
                blob=blob_name
            ).upload_blob(data, overwrite=True)
        
        return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"
    
    def list_files(self):
        container_client = self.blob_client.get_container_client(self.container_name)
        files = []
        
        for blob in container_client.list_blobs():
            files.append({
                "name": blob.name,
                "url": f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob.name}",
                "size": blob.size,
                "last_modified": blob.last_modified.isoformat()
            })
        
        return files
    
    def get_download_url(self, filename: str):
        return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{filename}"

blob_storage = BlobStorage()