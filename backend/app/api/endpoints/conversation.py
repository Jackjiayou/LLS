from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import traceback
from app.models.scene import scenes
from app.utils.search_vectorDB import vector_search
from app.utils import getds
from app.models.conversation import Message
from app.services.conversation_service import get_conversation_service
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


@router.post("/practice/save-json-message")
async def save_json_message(
        request: SaveJsonMessageRequest,
        token: dict = Depends(get_current_user),
        conversation_service=Depends(get_conversation_service)
):
    """保存聊天记录"""
    try:
        # 验证用户权限
        # practice = await conversation_service.get_practice_by_id(request.practice_id)
        # if not practice:
        #     raise HTTPException(status_code=404, detail="Practice not found")
        #
        # if str(token["sub"]) != str(practice.user_id):
        #     raise HTTPException(status_code=403, detail="Unauthorized access")

        # 保存聊天记录
        await conversation_service.save_json_message(request.practice_id, request.chat_history)
        return {"success": True, "message": "Chat history saved successfully"}
    except Exception as e:
        logger.error(f"保存聊天记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 新增练习相关的端点
@router.post("/practice/start", response_model=StartPracticeResponse)
async def start_practice(
    request: StartPracticeRequest,
    token: dict = Depends(get_current_user),
    conversation_service=Depends(get_conversation_service)
):
    """开始新的练习"""
    try:
        if str(token["sub"]) != str(request.userId):
            raise HTTPException(status_code=403, detail="Unauthorized access")

        result = await conversation_service.start_practice(
            user_id=request.userId,
            scenario_id=request.sceneId
        )
        return result
    except Exception as e:
        logger.error(f"开始练习失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/practice/message")
async def save_practice_message(
    request: SavePracticeMessageRequest,
    token: dict = Depends(get_current_user),
    conversation_service=Depends(get_conversation_service)
):
    """保存练习消息"""
    try:
        await conversation_service.save_message(request.practice_id, request.message)
        return {"message": "Message saved successfully"}
    except Exception as e:
        logger.error(f"保存消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/practice/end")
async def end_practice(
    request: EndPracticeRequest,
    token: dict = Depends(get_current_user),
    conversation_service=Depends(get_conversation_service)
):
    """结束练习"""
    try:
        await conversation_service.end_practice(request.practice_id, request.score_json)
        return {"message": "Practice ended successfully"}
    except Exception as e:
        logger.error(f"结束练习失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/practice/{practice_id}", response_model=PracticeHistoryResponse)
async def get_practice_history(
    practice_id: int,
    token: dict = Depends(get_current_user),
    conversation_service=Depends(get_conversation_service)
):
    """获取练习历史记录"""
    try:
        history = await conversation_service.get_practice_history(practice_id)
        return history
    except Exception as e:
        logger.error(f"获取练习历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



# 修改现有的 get_robot_message 端点，添加练习ID
@router.get("/get-robot-message")
async def get_robot_response(
        sceneId: int,
        messageCount: int,
        messages: Optional[str] = None,
        userId: Optional[str] = None,
        conversationId: Optional[str] = None,
        practiceId: Optional[int] = None,  # 新增练习ID参数
        token: dict = Depends(get_current_user),
        conversation_service=Depends(get_conversation_service)
):
    """获取机器人消息"""
    try:
        if userId and str(token["sub"]) != userId:
            raise HTTPException(status_code=403, detail="Unauthorized access")

        result = conversation_service.get_robot_message(
            sceneId,
            messageCount,
            messages,
            userId,
            conversationId,
            #practiceId  # 传递练习ID
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
        conversation_service=Depends(get_conversation_service)
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
        conversation_service=Depends(get_conversation_service)
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