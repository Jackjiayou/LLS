from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from datetime import datetime
import json
import traceback
import random
import  os
from app.models.conversation import Message
from app.services.conversation_service import (
    create_conversation,
    get_conversation,
    add_message,
    analyze_message,
    get_robot_message
)
from app.core.logger import logger, log_request, log_response, log_error
from app.core.config import settings
from app.utils.audio import convert_mp3_16k ,extract_words_from_lattice2
from  app.utils.personification_text_to_speach import text_to_speech as tts
from  app.utils.speech_to_text_fast import    speech_to_text as st

router = APIRouter()


@router.get("/get-robot-message")
async def get_robot_response(
    sceneId: int,
    messageCount: int,
    messages: Optional[str] = None,
    userId: Optional[str] = None,
    conversationId: Optional[str] = None
):
    """获取机器人消息"""
    try:
        result = get_robot_message(sceneId, messageCount, messages)
        return result
    except Exception as e:
        logger.error(f"获取机器人消息失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speech-to-text")
async def speech_to_text(audio_file: UploadFile = File(...), sceneId: int = Form(None), fileName: str = Form(None),
                         userId: str = Form(...),
                         conversationId: str = Form(...)):
    """
    将上传的语音文件转换为文本
    实际项目中应调用专业的语音识别API（如百度语音、讯飞语音等）

    此处为示例代码，真实实现时请替换为实际的语音识别API调用
    """
    # 使用传入的文件名或生成新的文件名
    if not fileName:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
        fileName = f"audio_{timestamp}_{random_str}.mp3"

    # 确保文件名有正确的扩展名
    if not fileName.endswith(('.wav', '.mp3', '.aac')):
        fileName += '.mp3'

    # 保存上传的文件
    file_location = f"{settings.file_path_voice}/{fileName}"
    #os.makedirs({settings.file_path_voice}, exist_ok=True)

    try:
        # 确保文件上传成功
        contents = await audio_file.read()
        with open(file_location, "wb") as f:
            f.write(contents)

        # 生成可访问的完整URL
        # 使用新的音频文件路由

        voice_url = f"{settings.voice_url}/{fileName}"
        local_url = os.path.join(settings.file_path_voice,fileName)
        # TODO: 此处调用您自己的语音识别API


        # 极速版
        # -----------------------------------------------------
        new_name = convert_mp3_16k(local_url)
        voice_url = f"{settings.voice_url}/{fileName}"

        new_local_url = fileName.replace('.mp3', '_16k.mp3')
        new_url =  os.path.join(settings.file_path_voice,new_name)
        str_result = st(new_url, settings.XUNFEI_APP_ID, settings.XUNFEI_API_KEY, settings.XUNFEI_API_SECRET)
        str_result = extract_words_from_lattice2(str_result)
        # --------------------------------

        # ------------------------------------------------
        #
        # str_result = st(local_url, settings.XUNFEI_APP_ID, settings.XUNFEI_API_KEY, settings.XUNFEI_API_SECRET)
        # str_result = extract_words_from_lattice2(str_result)
        # -----------------------------------------------------
        return {"text": str_result, "voiceUrl": voice_url}

    except Exception as e:
        logger.error(traceback.format_exc())
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"message": f"上传文件处理失败: {str(e)}"}
        )