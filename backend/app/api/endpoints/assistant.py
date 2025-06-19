from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import traceback
from app.models.scene import scenes
from app.utils.search_vectorDB import vector_search
from app.utils import getds
from app.models.conversation import AsisMessage
from app.services.assistant_service import get_assistant_service
from app.core.logger import logger, log_request, log_response, log_error
from app.core.config import settings
from app.utils.audio import convert_mp3_16k, extract_words_from_lattice2
from app.utils.personification_text_to_speach import text_to_speech as tts
from app.utils.speech_to_text_fast import speech_to_text as st
from app.schemas.practice import ChatMessage, SaveJsonMessageRequest
from app.core.auth import get_current_user
from app.schemas.practice import (
    StartPracticeRequest,
    StartPracticeResponse,
    PracticeMessage,
    SavePracticeMessageRequest,
    EndPracticeRequest,
    PracticeHistoryResponse
)

router = APIRouter()


# 修改现有的 get_robot_message 端点，添加练习ID
@router.get("/get-robot-message")
async def get_robot_response(
        messageCount: int,
        messages: Optional[str] = None,
        userId: Optional[str] = None,
        conversationId: Optional[str] = None,
        token: dict = Depends(get_current_user),
        conversation_service=Depends(get_assistant_service)
):
    """获取机器人消息"""
    try:
        if userId and str(token["sub"]) != userId:
            raise HTTPException(status_code=403, detail="Unauthorized access")

        result = conversation_service.get_robot_message(
            messageCount,
            messages,
            userId,
            conversationId
        )
        return result
    except Exception as e:
        logger.error(f"获取机器人消息失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# 修改现有的 speech_to_text 端点，添加练习ID
@router.post("/speech-to-text")
async def speech_to_text(
        audio_file: UploadFile = File(...),
        sceneId: int = Form(None),
        fileName: str = Form(None),
        userId: str = Form(...),
        conversationId: str = Form(...),
        practiceId: Optional[int] = Form(None),  # 新增练习ID参数
        token: dict = Depends(get_current_user),
        conversation_service=Depends(get_assistant_service)
):
    """将上传的语音文件转换为文本"""
    try:
        if str(token["sub"]) != userId:
            raise HTTPException(status_code=403, detail="Unauthorized access")

        contents = await audio_file.read()
        result = await conversation_service.speech_to_text(
            contents,
            sceneId,
            fileName,
            userId,
            conversationId,
            #practiceId  # 传递练习ID
        )
        return result

    except Exception as e:
        logger.error(traceback.format_exc())
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"message": f"上传文件处理失败: {str(e)}"}
        )


# 修改现有的 analyze 端点，添加练习ID
@router.post("/analyze")
async def analyze_message(
        request: Dict[str, Any],
        token: dict = Depends(get_current_user),
        conversation_service=Depends(get_assistant_service)
):
    """分析用户消息并生成改进建议"""
    try:
        message = request.get("message", "")
        scene_id = request.get("sceneId", 1)
        message_all = request['messages_all']
        user_id = request.get("userId")
        practice_id = request.get("practiceId")  # 新增练习ID

        if user_id and str(token["sub"]) != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized access")

        result = conversation_service.analyze_message(
            message,
            scene_id,
            json.loads(message_all),
            #practice_id  # 传递练习ID
        )
        return result
    except Exception as e:
        logger.error(f"分析消息失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))