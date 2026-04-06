# python/services/s3_boto3.py

import os
import uuid

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from python.models.modelos import *
import mimetypes

class S3Service:
    def __init__(self, use_local_profile=False, profile_name="default"):
        region = os.getenv("AWS_REGION") or "us-east-2"   # <-- Force region

        if use_local_profile:
            session = boto3.Session(profile_name=profile_name, region_name=region)
            self.s3_client = session.client("s3", region_name=region)
        else:
            self.s3_client = boto3.client(
                "s3",
                region_name="us-east-2",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                config=Config(s3={"addressing_style": "virtual"})
            )
        self.bucket_name = os.getenv("AWS_S3_BUCKET_NAME")

    def upload_file(self, file,file_uuid,tabla_origen):
        """
        Sube un archivo a S3 con un nombre UUID y lo guarda en la base de datos.

        :param file: Archivo a subir.
        :return: URL del archivo subido.
        """
        try:
            filename = file.filename
            filepath = f"{tabla_origen}/{file_uuid}_{filename}"
            # Subir a S3
            self.s3_client.upload_fileobj(file, self.bucket_name, filepath)
            return filename
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al subir el archivo: {e}")

    def generate_presigned_url(self, filepath,type, expiration=3600):
        """
        Genera una URL firmada para acceder al archivo de S3.

        :param filepath: La ruta del archivo en el bucket.
        :param expiration: Tiempo de expiración de la URL en segundos.
        :return: URL firmada.
        """
        try:
            if type=='view':
                mime_type = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
                response = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": filepath,"ResponseContentDisposition": "inline","ResponseContentType": mime_type},
                    ExpiresIn=expiration,
                )
            elif type=='download':
                response = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": filepath},
                    ExpiresIn=expiration,
                )                
            return response
        except ClientError as e:
            raise Exception(f"Error al generar la URL firmada: {e}")

    def delete_file(self, filepath):
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=filepath
            )
            return True
        except ClientError as e:
            raise Exception(f"Error al eliminar el archivo de S3: {e}")
            
    def read_file(self, filepath):
        try:
            obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=filepath)
            return obj["Body"].read().decode("utf-8")
        except Exception as e:
            raise Exception(f"Error al leer el archivo de S3: {e}")
