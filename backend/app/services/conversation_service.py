from datetime import datetime
import uuid
from typing import List, Optional, Dict, Any
import json
import random
import logging
import os
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
        os.makedirs(settings.BASE_DIR + "/tts", exist_ok=True)

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
            return {
                "suggestion": random.choice(suggestion_templates),
                "score": random.randint(70, 95)
            }

    def get_robot_message(self, scene_id: int, message_count: int, messages: Optional[str] = None) -> Dict[str, Any]:
        """获取机器人消息"""
        try:
            # 解析历史消息
            history_messages = []
            if messages:
                try:
                    history_messages = json.loads(messages)
                except:
                    pass

            # 如果是第一条消息（初始问候）
            if message_count == 0:
                return self._handle_initial_message(scene_id)
            else:
                return self._handle_followup_message(history_messages)

        except Exception as e:
            traceback.print_exc()
            logger.error(f"获取机器人消息失败: {str(e)}")
            raise

    def _handle_initial_message(self, scene_id: int) -> Dict[str, Any]:
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
            save_folder=self.file_path,
        )

        file_name = os.path.basename(file_name)
        y, sr = librosa.load(os.path.join(self.file_path, file_name), sr=None)
        duration = round(librosa.get_duration(y=y, sr=sr))
        file_path_url = self.base_url + '/' + file_name

        return {
            "text": text,
            "duration": duration,
            "voiceUrl": file_path_url
        }

    def _handle_followup_message(self, history_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
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
            save_folder=self.file_path
        )

        file_name = os.path.basename(file_name)
        y, sr = librosa.load(os.path.join(self.file_path, file_name), sr=None)
        duration = round(librosa.get_duration(y=y, sr=sr))
        file_path_url = self.base_url + '/' + file_name

        return {
            "text": robot_words,
            "duration": duration,
            "voiceUrl": file_path_url
        }

    async def speech_to_text(self, audio_file: bytes, scene_id: Optional[int] = None, file_name: Optional[str] = None) -> Dict[str, Any]:
        """将语音文件转换为文本"""
        try:
            # 使用传入的文件名或生成新的文件名
            if not file_name:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
                file_name = f"audio_{timestamp}_{random_str}.mp3"

            # 确保文件名有正确的扩展名
            if not file_name.endswith(('.wav', '.mp3', '.aac')):
                file_name += '.mp3'

            # 保存上传的文件
            file_location = f"{settings.file_path_voice}/{file_name}"
            os.makedirs(settings.file_path_voice, exist_ok=True)

            # 确保文件上传成功
            with open(file_location, "wb") as f:
                f.write(audio_file)

            # 生成可访问的完整URL
            voice_url = f"{settings.voice_url}/{file_name}"
            local_url = os.path.join(settings.file_path_voice, file_name)

            # 极速版
            new_name = convert_mp3_16k(local_url)
            new_local_url = file_name.replace('.mp3', '_16k.mp3')
            new_url = os.path.join(settings.file_path_voice, new_name)
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

