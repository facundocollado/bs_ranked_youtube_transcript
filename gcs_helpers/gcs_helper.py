import os
from google.cloud import storage

class GCSHelper:
    def __init__(self):
        self.project_id = os.getenv("PROJECT_ID", "bs-ranked")
        self.bucket_name = f"{self.project_id}-bucket"
        self.storage_client = storage.Client(project=self.project_id)
        self.bucket = self._get_or_create_bucket() 

    def _get_or_create_bucket(self):
        try:
            bucket = self.storage_client.get_bucket(self.bucket_name)
        except Exception:
            bucket = self.storage_client.create_bucket(self.bucket_name)
        return bucket

    def upload_file(self, local_path: str, remote_path: str) -> str:
        """
        Upload a file to the GCS bucket.
        
        Args:
            local_path (str): Local file path to upload.
            remote_path (str): Path in the GCS bucket.
        
        Returns:
            str: GCS path of the uploaded file.
        """

        blob = self.bucket.blob(remote_path)
        blob.upload_from_filename(local_path)
        return f"gs://{self.bucket_name}/{remote_path}"

    def file_exists(self, remote_path: str) -> bool:
        return self.bucket.blob(remote_path).exists()

    def list_files(self, prefix: str = ""):
        return [blob.name for blob in self.bucket.list_blobs(prefix=prefix)]