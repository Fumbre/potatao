import boto3
import threading
import datetime
from mypy_boto3_s3 import S3Client
from common.aws3.file_type import FileType
from typing import Dict,TypedDict,List


class SessionData(TypedDict):
    UploadId: str
    Bucket: str
    Key: str
    Parts: List[dict]
    Buffer: bytearray
    last_active_time: datetime.datetime

class S3Util:
    _instance = None
    _lock = threading.Lock()
    _client:S3Client =  None
    _active_sessions:Dict[str,SessionData] = {}
    _CHUNK_THRESHOLD = 5 * 1024 * 1024
    
    @classmethod
    def init(cls,ip:str,port:str,access_key:str,secret_key:str):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls.__new__(cls)
                    endpoint = f"http://{ip}:{port}"
                    cls._client = boto3.client(
                        "s3",
                        endpoint_url = endpoint,
                        aws_access_key_id = access_key,
                        aws_secret_access_key = secret_key,
                        region_name = "eu-east-1"
                    )
        return cls._instance
    
    @classmethod
    def start_session(cls,machine_id:str,user_id:str,bucket_name:str,content_type:FileType)->str:
        current_timestamp = datetime.datetime.now().timestamp()
        session_id = f"{user_id}_{machine_id}_{current_timestamp}"
        key = f"{session_id}.{content_type.ext}"
        date = datetime.datetime.now().strftime("%Y%m%d")
        path = f"{user_id}/{date}/{key}"
        response = cls._client.create_multipart_upload(
            Bucket=bucket_name,
            Key=path,
            ContentType= content_type.mime
        )
        upload_id = response["UploadId"]
        with cls._lock:
            cls._active_sessions[session_id] = {
                "UploadId":upload_id,
                "Bucket":bucket_name,
                "Key":path,
                "Parts":[],
                "Buffer":bytearray(),
                "last_active_time":datetime.datetime.now()
            }
        return session_id
    
    
    @classmethod
    def upload_parts(cls, session_id:str,data:bytes):
        session = cls._active_sessions.get(session_id)
        if session:
            session["Buffer"].extend(data)
            session["last_active_time"] = datetime.datetime.now()
            if len(session["Buffer"]) >= cls._CHUNK_THRESHOLD:
                current_part_number = len(session["Parts"]) + 1
                response = cls._client.upload_part(
                    Bucket=session["Bucket"],
                    Key=session["Key"],
                    UploadId=session["UploadId"],
                    PartNumber=current_part_number,
                    Body=bytes(session["Buffer"])
                )
                session["Parts"].append({
                    "ETag":response["ETag"],
                    "Partnumber":current_part_number
                })
                session["Buffer"].clear()
    
    
    @classmethod
    def complete_session(cls,session_id:str)->str:
        session = cls._active_sessions[session_id]
        if session:
            if len(session["Buffer"]) > 0:
                last_part_number = len(session["Parts"]) + 1
                response = cls._client.upload_part(
                    Bucket=session["Bucket"],
                    Key=session["Key"],
                    UploadId=session["UploadId"],
                    PartNumber=last_part_number,
                    Body=bytes(session["Buffer"])
                )            
                session["Parts"].append({
                    "ETag": response["ETag"],
                    "PartNumber": last_part_number
                })
            
            if session["Parts"]:
                cls._client.complete_multipart_upload(
                    Bucket=session["Bucket"],
                    Key=session["Key"],
                    UploadId=session["UploadId"],
                    MultipartUpload={"Parts":session["Parts"]}
                )
            else:
                cls._client.abort_multipart_upload(
                    Bucket=session["Bucket"],
                    Key=session["Key"],
                    UploadId=session["UploadId"]
                )
        return session["Key"]                                    