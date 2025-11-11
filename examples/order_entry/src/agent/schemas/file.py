import base64
import os
from pydantic import BaseModel
from typing import Optional
# from s3_client import S3Client

class S3Client:
    def __init__(self, environment: str):
        self.env = environment

    def download(self, s3_link):
        pass

    def upload(self, s3_link):
        pass


class StateFile(BaseModel):
    title: str
    s3_link: str
    
    def as_bytes(self) -> bytes:
        """Fetch the file from S3 and return its content as bytes."""
        environment = os.getenv("ENV")
        client = S3Client(env=environment)
        _, base64_data = client.download(self.s3_link)
        return base64.b64decode(base64_data)

    def as_base64(self) -> str:
        """Fetch the file from S3 and return its content as a base64-encoded string."""
        environment = os.getenv("ENV")
        client = S3Client(env=environment)
        _, base64_data = client.download(self.s3_link)
        return base64_data