import json

from sqlalchemy.orm import Session
from sqlalchemy import select

from common.aws3.file_type import FileType
from common.aws3.s3 import S3Util
from common.encrptytion.aes.aes import AESUtil
from common.redis.redis import RedisClient
from model.llm_model import Language, UserLanguage
from model.pico_device_model import PicoDevice
from ws.ws_manager import WebsocketManager


def store_pefered_language(machine_id:str,lang:str,db:Session)->dict:
    ## get pico device and language info
    pico:PicoDevice = db.scalar(select(PicoDevice).where(PicoDevice.machine_id == machine_id))
    language:Language  = db.scalar(select(Language).where(Language.iso_code == lang))
    ## get pico and language relationship
    user_lang:UserLanguage = db.scalar(select(UserLanguage).where(UserLanguage.pico_id == pico.id))
    print(language.id)
    if user_lang:
        user_lang.language_id = language.id
    else:
        user_lang = UserLanguage(pico_id=pico.id,language_id=language.id)
        db.add(user_lang)
    db.commit()
    # get user language list
    sql = (select(PicoDevice.machine_id,Language.iso_code,Language.binary_code)
           .join(UserLanguage,PicoDevice.id == UserLanguage.pico_id)
           .join(Language,UserLanguage.language_id == Language.id).where(PicoDevice.machine_id != machine_id))
    result =  db.execute(sql).all()
    data = {}
    for machine,iso,binary_code in result:
        print(type(binary_code), repr(binary_code))
        row = {}
        row['lang'] = iso
        row['binary_code'] = ord(binary_code) if isinstance(binary_code, (bytes, str)) and len(
            binary_code) == 1 else binary_code
        data[machine] = row

    ## put this into redis
    RedisClient.set("user_language",json.dumps(data))
    return data


def start_translated_audio_session(original_machine_id,language_dict:dict,key:str):
    session_id_list = {}
    for machine_id in language_dict:
        session_id = S3Util.start_session(machine_id=machine_id,user_id=key,bucket_name="translated-audio",content_type=FileType.WAV)
        binary = language_dict[machine_id]["binary_code"]
        session_id_list[str(binary)] = session_id

    RedisClient.set(f"user_translated_session:{original_machine_id}",json.dumps(session_id_list))


def stop_translated_audio_session(machine_id:str):

    session_id_list:dict = json.loads(RedisClient.get(f"user_translated_session:{machine_id}"))
    for session_id in session_id_list:

        S3Util.complete_session(session_id_list[session_id])

    RedisClient.delete(f"user_translated_session:{machine_id}")


def construct(data:bytes,websocket_manager:WebsocketManager,machine_id:str)->bytes:
   ws =  websocket_manager.active_sessions
   machines = []
   for machine in ws:
       if machine != machine_id:
           machines.append(machine)
   final_data = bytearray()
   final_data.append(data[0])
   # get language list in Redis
   # languages_list = json.loads(RedisClient.get(f"user_language"))
   # length = len(languages_list)
   final_data.append(1)
   final_data.append(0x01)
   # for language in languages_list:
   #     final_data.append(language["binary_code"])
   audio_data = data[9:]
   final_data.extend(audio_data)
   key = RedisClient.get(f"llm_data_key:{machine_id}")
   return AESUtil.encrypt_bytes(key,final_data)
