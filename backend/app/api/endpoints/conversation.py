from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from datetime import datetime
import json
import traceback

from app.models.conversation import Message
from app.services.conversation_service import (
    create_conversation,
    get_conversation,
    add_message,
    analyze_message,
    get_robot_message
)
from app.core.logger import logger, log_request, log_response, log_error

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

