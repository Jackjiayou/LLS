from datetime import datetime
import uuid
from typing import List, Optional, Dict, Any
import json
import random
import logging
import os
from sqlalchemy import func
import traceback
import librosa
from app.models.conversation import Conversation, Message
from ..core.config import settings
from ..utils import getds
from ..models import scene
from ..utils.personification_text_to_speach import text_to_speech
from app.core.logger import logger, log_request, log_response, log_error
from app.utils.search_vectorDB import vector_search
from app.utils.audio import convert_mp3_16k, extract_words_from_lattice2
from app.utils.speech_to_text_fast import speech_to_text as st
from app.models.practice import PracticeRecord, PracticeMessage
from app.db.database import SessionLocal
from app.schemas.practice import (
    StartPracticeRequest,
    StartPracticeResponse,
    PracticeMessage,
    SavePracticeMessageRequest,
    EndPracticeRequest,
    PracticeHistoryResponse
)

# 改进建议模板
suggestion_templates = [
    "在回答客户问题前，可以先简短重复一下客户的问题，表明您理解了他们的需求。",
    "增加具体案例和数据支持，提高说服力。可以准备2-3个成功案例，在合适的时机分享。",
    "适当使用反问句引导客户思考，这样的问题可以引导客户从新的角度看问题。",
    "在谈到产品优势时，可以结合客户所处的行业情况，使建议更有针对性。",
    "练习如何简洁有力地总结对话内容，在每个销售环节结束时进行小结，帮助客户和自己明确当前进展。"
]

class ConversationService:
    def __init__(self):
        self.base_url = settings.BASE_URL + "/uploads/tts/"
        self.file_path = settings.file_path_tts
        # 创建基础目录
        self.current_practice_id = None
        os.makedirs(settings.BASE_DIR + "/tts", exist_ok=True)
        os.makedirs(settings.BASE_DIR + "/voice", exist_ok=True)

    async def start_practice(self, user_id: int, scenario_id: int) -> Dict[str, Any]:
        """开始新的练习"""
        try:
            with SessionLocal() as db:
                practice = PracticeRecord(
                    user_id=user_id,
                    scenario_id=scenario_id,
                    status='in_progress'
                )
                db.add(practice)
                db.commit()
                db.refresh(practice)

                self.current_practice_id = practice.practice_id
                return {
                    "practice_id": practice.practice_id,
                    "started_at": practice.started_at
                }
        except Exception as e:
            logger.error(f"开始练习失败: {str(e)}")
            traceback.print_exc()
            raise

    async def save_json_message(self, practice_id: int, messages: List[Dict[str, Any]]) -> None:
        """保存单条消息"""
        try:
            #chat_history  = json.dumps(message, ensure_ascii=False)
            with SessionLocal() as db:
                # 获取练习记录
                practice = db.query(PracticeRecord) \
                    .filter(PracticeRecord.practice_id == practice_id) \
                    .first()

                if not practice:
                    raise ValueError(f"Practice record not found: {practice_id}")

                # 直接更新整个 chat_history
                message_list = []
                for msg in messages:
                    message_dict = {
                        "from": msg.from_,  # 注意这里使用 from_ 因为 from 是 Python 关键字
                        "text": msg.text,
                        "voiceUrl": msg.voiceUrl,
                        "duration": msg.duration,
                        "suggestion": msg.suggestion,
                        "timestamp": msg.timestamp
                    }
                    message_list.append(message_dict)

                practice.chat_history = message_list
                practice.updated_at = datetime.utcnow()

                # 提交更改
                db.commit()

            logger.info(f"Successfully saved chat history for practice {practice_id}")
        except Exception as e:
            logger.error(f"保存消息失败: {str(e)}")
            raise

    async def save_message(self, practice_id: int, message: Dict[str, Any]) -> None:
        """保存单条消息"""
        try:
            with SessionLocal() as db:
                # 获取当前最大消息序号
                max_order = db.query(func.max(PracticeMessage.message_order)) \
                                .filter(PracticeMessage.practice_id == practice_id) \
                                .scalar() or 0

                # 创建新消息记录
                practice_message = PracticeMessage(
                    practice_id=practice_id,
                    message_type=message['from'],
                    content=message['text'],
                    voice_url=message.get('voiceUrl'),
                    duration=message.get('duration'),
                    suggestion=message.get('suggestion'),
                    message_order=max_order + 1
                )
                db.add(practice_message)

                # 更新练习记录的更新时间
                practice = db.query(PracticeRecord) \
                    .filter(PracticeRecord.practice_id == practice_id) \
                    .first()
                if practice:
                    practice.updated_at = datetime.utcnow()

                db.commit()
        except Exception as e:
            logger.error(f"保存消息失败: {str(e)}")
            traceback.print_exc()
            raise

    async def end_practice(self, practice_id: int, score_json: Optional[Dict[str, Any]] = None) -> None:
        """结束练习"""
        try:
            with SessionLocal() as db:
                practice = db.query(PracticeRecord) \
                    .filter(PracticeRecord.practice_id == practice_id) \
                    .first()
                if not practice:
                    raise ValueError(f"Practice {practice_id} not found")

                practice.status = 'completed'
                practice.ended_at = datetime.utcnow()
                if score_json:
                    practice.score_json = score_json

                db.commit()
        except Exception as e:
            logger.error(f"结束练习失败: {str(e)}")
            traceback.print_exc()
            raise

    async def get_practice_history(self, practice_id: int) -> Dict[str, Any]:
        """获取练习历史记录"""
        try:
            with SessionLocal() as db:
                practice = db.query(PracticeRecord) \
                    .filter(PracticeRecord.practice_id == practice_id) \
                    .first()
                if not practice:
                    raise ValueError(f"Practice {practice_id} not found")

                messages = db.query(PracticeMessage) \
                    .filter(PracticeMessage.practice_id == practice_id) \
                    .order_by(PracticeMessage.message_order) \
                    .all()

                return {
                    "practice_id": practice.practice_id,
                    "user_id": practice.user_id,
                    "scenario_id": practice.scenario_id,
                    "started_at": practice.started_at,
                    "ended_at": practice.ended_at,
                    "status": practice.status,
                    "score_json": practice.score_json,
                    "messages": [
                        {
                            "from": msg.message_type,
                            "text": msg.content,
                            "voiceUrl": msg.voice_url,
                            "duration": msg.duration,
                            "suggestion": msg.suggestion,
                            "timestamp": msg.created_at
                        }
                        for msg in messages
                    ]
                }
        except Exception as e:
            logger.error(f"获取练习历史失败: {str(e)}")
            traceback.print_exc()
            raise

    def _get_user_paths(self, user_id: str, conversation_id: Optional[str] = None) -> Dict[str, str]:
        """获取用户相关的文件路径"""
        # 基础路径
        base_tts_path = os.path.join(settings.UPLOAD_DIR, "tts", user_id)
        base_voice_path = os.path.join(settings.UPLOAD_DIR, "voice", user_id)

        # 如果提供了会话ID，则创建会话子目录
        if conversation_id:
            tts_path = os.path.join(base_tts_path, conversation_id)
            voice_path = os.path.join(base_voice_path, conversation_id)
        else:
            tts_path = base_tts_path
            voice_path = base_voice_path

        # 创建目录
        os.makedirs(tts_path, exist_ok=True)
        os.makedirs(voice_path, exist_ok=True)

        # 返回URL路径
        return {
            "tts_path": tts_path,
            "voice_path": voice_path,
            "tts_url": f"{settings.BASE_URL}/uploads/tts/{user_id}/{conversation_id if conversation_id else ''}",
            "voice_url": f"{settings.BASE_URL}/uploads/voice/{user_id}/{conversation_id if conversation_id else ''}"
        }

    def analyze_message(self, message: str, scene_id: int, messages_all: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析用户消息并生成改进建议"""
        try:
            # 获取最后一条用户消息
            last_customer_text = None
            for entry in reversed(messages_all):
                if entry.get("from") == "customer":
                    last_customer_text = entry.get("text")
                    break

            # 根据场景ID选择不同的分析策略
            db_path = settings.vec_db_nucleotide if scene_id == 0 else settings.vec_db_production

            # 调用向量搜索获取相关上下文
            result_msg = vector_search(query=f"{last_customer_text}", db_path=db_path, k=3)

            # 构建上下文信息
            q_msg = ''
            if len(result_msg) > 0:
                for it in result_msg:
                    q_msg = q_msg + "---------------------------------\n" + it.page_content
            q_msg = f'<<<{q_msg}>>>'
            # 调用大模型进行分析
            msg = getds.get_messages_analyze(messages_all, q_msg, scene_id)
            robot_words = getds.get_response_qwen(msg)

            return {
                "suggestion": robot_words,
                "score": random.randint(70, 95)
            }
        except Exception as e:
            logger.error(f"分析消息失败: {str(e)}")
            traceback.print_exc()
            raise

    def get_robot_message(self, scene_id: int, message_count: int, messages: Optional[str] = None, user_id: Optional[str] = None, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """获取机器人消息"""
        try:
            # 解析历史消息
            history_messages = []
            if messages:
                try:
                    history_messages = json.loads(messages)
                except:
                    pass

            # 获取用户路径
            paths = self._get_user_paths(user_id, conversation_id) if user_id else {
                "tts_path": self.file_path,
                "tts_url": self.base_url
            }

            # 如果是第一条消息（初始问候）
            if message_count == 0:
                return self._handle_initial_message(scene_id, paths)
            else:
                return self._handle_followup_message(history_messages, paths)

        except Exception as e:
            traceback.print_exc()
            logger.error(f"获取机器人消息失败: {str(e)}")
            raise

    def _handle_initial_message(self, scene_id: int, paths: Dict[str, str]) -> Dict[str, Any]:
        """处理初始问候消息"""
        scene_questions = scene.questions.get(scene_id, [])
        if not scene_questions:
            raise ValueError(f"No questions found for scene {scene_id}")

        question = random.choice(scene_questions)
        text = question["text"]

        file_name = text_to_speech(
            text=text,
            appid=settings.XUNFEI_APP_ID,
            apisecret=settings.XUNFEI_API_SECRET,
            apikey=settings.XUNFEI_API_KEY,
            save_folder=paths["tts_path"],
        )

        file_name = os.path.basename(file_name)
        y, sr = librosa.load(os.path.join(paths["tts_path"], file_name), sr=None)
        duration = round(librosa.get_duration(y=y, sr=sr))
        file_path_url = f"{paths['tts_url']}/{file_name}"

        return {
            "text": text,
            "duration": duration,
            "voiceUrl": file_path_url
        }

    def _handle_followup_message(self, history_messages: List[Dict[str, Any]], paths: Dict[str, str]) -> Dict[str, Any]:
        """处理后续消息"""
        if not history_messages:
            raise ValueError("No history messages provided")

        last_message = history_messages[-1]
        if last_message["from"] != "user":
            raise ValueError("Last message is not from user")

        chat_msg = getds.get_messages_ai(json.dumps(history_messages))
        robot_words = getds.get_response_qwen(chat_msg)

        file_name = text_to_speech(
            text=robot_words,
            appid=settings.XUNFEI_APP_ID,
            apisecret=settings.XUNFEI_API_SECRET,
            apikey=settings.XUNFEI_API_KEY,
            save_folder=paths["tts_path"]
        )

        file_name = os.path.basename(file_name)
        y, sr = librosa.load(os.path.join(paths["tts_path"], file_name), sr=None)
        duration = round(librosa.get_duration(y=y, sr=sr))
        file_path_url = f"{paths['tts_url']}/{file_name}"

        return {
            "text": robot_words,
            "duration": duration,
            "voiceUrl": file_path_url
        }

    async def speech_to_text(self, audio_file: bytes, scene_id: Optional[int] = None, file_name: Optional[str] = None, user_id: Optional[str] = None, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """将语音文件转换为文本"""
        try:
            # 获取用户路径
            paths = self._get_user_paths(user_id, conversation_id) if user_id else {
                "voice_path": settings.file_path_voice,
                "voice_url": settings.voice_url
            }

            # 使用传入的文件名或生成新的文件名
            if not file_name:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
                file_name = f"audio_{timestamp}_{random_str}.mp3"

            # 确保文件名有正确的扩展名
            if not file_name.endswith(('.wav', '.mp3', '.aac')):
                file_name += '.mp3'

            # 保存上传的文件
            file_location = os.path.join(paths["voice_path"], file_name)
            os.makedirs(os.path.dirname(file_location), exist_ok=True)

            # 确保文件上传成功
            with open(file_location, "wb") as f:
                f.write(audio_file)

            # 生成可访问的完整URL
            voice_url = f"{paths['voice_url']}/{file_name}"
            local_url = file_location

            # 极速版
            new_name = convert_mp3_16k(local_url)
            new_local_url = file_name.replace('.mp3', '_16k.mp3')
            new_url = os.path.join(paths["voice_path"], new_name)
            str_result = st(new_url, settings.XUNFEI_APP_ID, settings.XUNFEI_API_KEY, settings.XUNFEI_API_SECRET)
            str_result = extract_words_from_lattice2(str_result)

            return {"text": str_result, "voiceUrl": voice_url}

        except Exception as e:
            logger.error(traceback.format_exc())
            traceback.print_exc()
            raise Exception(f"上传文件处理失败: {str(e)}")

# 新增依赖注入工厂
def get_conversation_service():
    return ConversationService()

