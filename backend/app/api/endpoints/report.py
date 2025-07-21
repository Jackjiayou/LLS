from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends,Body
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
from app.services.conversation_service import  get_conversation_service
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
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    html_path = settings.html_path
    return FileResponse(html_path)


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
            # practice_id  # 传递练习ID
        )
        return result
    except Exception as e:
        logger.error(f"分析消息失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-practice")
async def analyze_practice(
    request: dict = Body(...),
    token: dict = Depends(get_current_user),
    conversation_service=Depends(get_conversation_service)
):
    """
    对练习进行分析打分，返回各项分数和分析文本
    """
    try:
        practice_id = request.get("practice_id")
        conversation_id = request.get("conversationId")
        user_id = str(token["sub"])
        result = conversation_service.analyze_practice(practice_id,conversation_id,user_id)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"分析练习失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
