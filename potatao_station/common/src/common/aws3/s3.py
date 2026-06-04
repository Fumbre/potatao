import struct
import boto3
import threading
import datetime
from mypy_boto3_s3 import S3Client
from common.aws3.file_type import FileType
from typing import Dict, TypedDict, List


class SessionData(TypedDict):
    UploadId: str
    Bucket: str
    Key: str
    Parts: List[dict]
    Buffer: bytearray
    last_active_time: datetime.datetime
    total_bytes_written: int


class S3Util:
    _instance = None
    _lock = threading.Lock()
    _client: S3Client = None
    _active_sessions: Dict[str, SessionData] = {}
    _CHUNK_THRESHOLD = 5 * 1024 * 1024

    @classmethod
    def init(cls, ip: str, port: str, access_key: str, secret_key: str):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls.__new__(cls)
                    endpoint = f"http://{ip}:{port}"
                    cls._client = boto3.client(
                        "s3",
                        endpoint_url=endpoint,
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key,
                        region_name="eu-east-1"
                    )
        return cls._instance

    @classmethod
    def start_session(cls, machine_id: str, user_id: str, bucket_name: str, content_type: FileType) -> str:
        session_id = f"{user_id}_{machine_id}_{datetime.datetime.now().timestamp()}"
        key = f"{session_id}.{content_type.ext}"
        path = f"{user_id}/{datetime.datetime.now().strftime('%Y%m%d')}/{key}"

        response = cls._client.create_multipart_upload(Bucket=bucket_name, Key=path, ContentType=content_type.mime)

        # 0xFFFFFFFF tells the player to read until EOF, ignoring the length metadata
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
                             b'RIFF', 0xFFFFFFFF, b'WAVE', b'fmt ', 16, 1, 1,
                             24000, 48000, 2, 16,  #
                             b'data', 0xFFFFFFFF)

        with cls._lock:
            cls._active_sessions[session_id] = {
                "UploadId": response["UploadId"],
                "Bucket": bucket_name,
                "Key": path,
                "Parts": [],
                "Buffer": bytearray(header),
                "last_active_time": datetime.datetime.now(),
                "total_bytes_written": 0
            }
        return session_id

    @classmethod
    def upload_parts(cls, session_id: str, data: bytes):
        if len(data) % 2 != 0:
            data = data[:-1]

        with cls._lock:
            session = cls._active_sessions.get(session_id)
            if not session:
                print(f"[S3] session not found: {session_id}")
                return

            session["Buffer"].extend(data)
            session["total_bytes_written"] += len(data)
            session["last_active_time"] = datetime.datetime.now()

            if len(session["Buffer"]) >= cls._CHUNK_THRESHOLD:
                cls._flush_part(session)

    @classmethod
    def _flush_part(cls, session: SessionData):
        part_number = len(session["Parts"]) + 1
        response = cls._client.upload_part(
            Bucket=session["Bucket"],
            Key=session["Key"],
            UploadId=session["UploadId"],
            PartNumber=part_number,
            Body=bytes(session["Buffer"])
        )
        session["Parts"].append({"ETag": response["ETag"], "PartNumber": part_number})
        session["Buffer"].clear()

    @classmethod
    def complete_session(cls, session_id: str) -> str:
        with cls._lock:
            session = cls._active_sessions.get(session_id)
            if not session: return None
            print(session["total_bytes_written"])
            if len(session["Buffer"]) > 0:
                cls._flush_part(session)

            cls._client.complete_multipart_upload(
                Bucket=session["Bucket"],
                Key=session["Key"],
                UploadId=session["UploadId"],
                MultipartUpload={"Parts": session["Parts"]}
            )
            return cls._active_sessions.pop(session_id)["Key"]