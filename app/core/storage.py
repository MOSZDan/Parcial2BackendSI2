import aioboto3
from fastapi import UploadFile
import uuid
from .config import settings

async def upload_file_to_s3(file: UploadFile, folder: str = "evidencias") -> str:
    session = aioboto3.Session()
    
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{folder}/{uuid.uuid4()}.{file_extension}"
    
    async with session.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    ) as s3_client:
        await s3_client.upload_fileobj(
            file.file,
            settings.S3_BUCKET,
            unique_filename,
            ExtraArgs={"ContentType": file.content_type, "ACL": "public-read"}
        )
        
    # Construir URL pública (para Supabase Storage)
    public_url = f"{settings.S3_ENDPOINT.replace('/s3', '/object/public')}/{settings.S3_BUCKET}/{unique_filename}"
    return public_url
