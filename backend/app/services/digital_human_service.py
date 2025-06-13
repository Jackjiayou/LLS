import os
import uuid
import random
import librosa
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import UploadFile
from app.core.config import settings
from app.core.logging import logger
from app.models.digital_human import DigitalHumanMessage, DigitalHumanConversation, digital_human_conversations
from app.utils.speech import text_to_speech, speech_to_text
from app.utils.video import process_video

async def create_conversation(user_id: str) -> DigitalHumanConversation:
    """创建新的数字人对话"""
    try:
        conversation_id = str(uuid.uuid4())
        conversation = DigitalHumanConversation(
            id=conversation_id,
            user_id=user_id,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        digital_human_conversations[conversation_id] = conversation
        return conversation
    except Exception as e:
        logger.error(f"创建数字人对话失败: {str(e)}")
        raise

async def get_conversation(conversation_id: str) -> DigitalHumanConversation:
    """获取数字人对话"""
    conversation = digital_human_conversations.get(conversation_id)
    if not conversation:
        raise ValueError(f"Conversation {conversation_id} not found")
    return conversation

async def add_message(conversation_id: str, message: DigitalHumanMessage) -> DigitalHumanConversation:
    """添加消息到数字人对话"""
    try:
        conversation = await get_conversation(conversation_id)
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        return conversation
    except Exception as e:
        logger.error(f"添加消息失败: {str(e)}")
        raise

async def process_speech_to_text(audio_file: UploadFile, user_id: str, conversation_id: str) -> Dict[str, str]:
    """处理语音转文字"""
    try:
        # 确保上传目录存在
        os.makedirs("uploads/voice", exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
        file_name = f"audio_{timestamp}_{random_str}.mp3"
        file_location = f"uploads/voice/{file_name}"
        
        # 保存上传的文件
        contents = await audio_file.read()
        with open(file_location, "wb") as f:
            f.write(contents)
        
        # 调用语音识别服务
        text = await speech_to_text(file_location)
        
        # 生成可访问的URL
        voice_url = f"{settings.BASE_URL}/uploads/voice/{file_name}"
        
        return {
            "text": text,
            "voiceUrl": voice_url
        }
    except Exception as e:
        logger.error(f"语音转文字失败: {str(e)}")
        raise

async def generate_digital_human_response(
    text: str,
    messages: Optional[str] = None,
    user_id: Optional[str] = None,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """生成数字人响应"""
    try:
        # 解析历史消息
        history_messages = []
        if messages:
            try:
                history_messages = json.loads(messages)
            except:
                pass
        
        # 生成回复文本
        chat_msg = getds.get_messages_ai(messages)
        response_text = getds.get_response_qwen(chat_msg)
        
        # 生成语音
        file_path = './uploads/tts/'
        os.makedirs(file_path, exist_ok=True)
        file_name = text_to_speech(response_text, settings.APP_ID, settings.API_SECRET, settings.API_KEY, file_path)
        
        # 计算音频时长
        y, sr = librosa.load(file_path + file_name, sr=None)
        duration = round(librosa.get_duration(y=y, sr=sr))
        
        # 生成视频
        video_path = f'./uploads/download/{random.choice(["tp4.mp4", "tp2.mp4", "tp3.mp4"])}'
        local_audio_path = file_path + file_name
        video_path_combine = process_video(video_path, local_audio_path, settings.VIDEO_API_URL)
        
        # 生成URL
        file_name = os.path.basename(file_name)
        voice_url = f"{settings.BASE_URL}/uploads/tts/{file_name}"
        video_url = f"{settings.BASE_URL}/uploads/download/{os.path.basename(video_path_combine)}"
        
        return {
            "text": response_text,
            "duration": duration,
            "voiceUrl": voice_url,
            "videoUrl": video_url
        }
    except Exception as e:
        logger.error(f"生成数字人响应失败: {str(e)}")
        raise 