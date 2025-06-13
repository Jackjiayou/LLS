from datetime import datetime
import uuid
from typing import List, Optional, Dict, Any
import json
import random
import logging
from app.models.conversation import Conversation, Message, conversations, suggestion_templates
from ..core.config import settings
from ..utils import getds
from ..models import scene
from ..utils.personification_text_to_speach  import text_to_speech
import librosa
import  traceback
from app.core.logger import logger, log_request, log_response, log_error

def create_conversation(user_id: str, scene_id: int) -> Conversation:
    """创建新的对话"""
    conversation_id = str(uuid.uuid4())
    conversation = Conversation(
        id=conversation_id,
        user_id=user_id,
        scene_id=scene_id,
        messages=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    conversations[conversation_id] = conversation
    return conversation


def get_conversation(conversation_id: str) -> Optional[Conversation]:
    """获取指定对话"""
    return conversations.get(conversation_id)


def add_message(conversation_id: str, message: Message) -> Optional[Conversation]:
    """添加消息到对话"""
    conversation = conversations.get(conversation_id)
    if conversation:
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        return conversation
    return None


def analyze_message(message: str, scene_id: int, messages_all: List[Dict[str, Any]]) -> Dict[str, Any]:
    """分析用户消息并生成改进建议"""
    try:
        # 获取最后一条用户消息
        last_customer_text = None
        for entry in reversed(messages_all):
            if entry.get("from") == "customer":
                last_customer_text = entry.get("text")
                break

        # 根据场景ID选择不同的分析策略
        if scene_id == 0:
            db_path = './db/fund_nucleotide_chunk'
        else:
            db_path = './db/fund_production_chunk'

        # 调用向量搜索获取相关上下文
        from app.utils.search_vectorDB import vector_search
        result_msg = vector_search(query=f"{last_customer_text}", db_path=db_path, k=3)

        # 构建上下文信息
        q_msg = ''
        if len(result_msg) > 0:
            for it in result_msg:
                q_msg = q_msg + "---------------------------------\n" + it.page_content

        # 调用大模型进行分析
        from app.utils.getds import get_messages_analyze, get_response_qwen
        msg = get_messages_analyze(messages_all, q_msg, scene_id)
        robot_words = get_response_qwen(msg)

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

def get_robot_message(sceneId: int, messageCount: int, messages: Optional[str] = None) -> Dict[str, Any]:
    """获取机器人消息"""
    import  os
    try:
        print('get_robot_message')
        print("get_robot_message start")
        # 确保上传目录存在
        os.makedirs(settings.BASE_DIR+"/tts", exist_ok=True)

        # 设置基础URL，使用单斜杠
        base_url = settings.BASE_URL + "/uploads/tts/"

        # 解析历史消息
        history_messages = []
        if messages:
            try:
                history_messages = json.loads(messages)
            except:
                pass

        # 模拟大模型生成回复
        # 在实际应用中，这里应该调用大模型API
        # 这里我们根据消息数量和场景ID选择不同的回复策略

        # 如果是第一条消息（初始问候）
        file_path= settings.file_path_tts
        if messageCount == 0:
            # 从问题库中随机选择一个初始问题
            scene_questions = scene.questions.get(sceneId, [])
            if scene_questions:
                question = random.choice(scene_questions)
                text = question["text"]

                file_name = text_to_speech(
                    text=text,
                    appid=settings.XUNFEI_APP_ID,
                    apisecret=settings.XUNFEI_API_SECRET,
                    apikey=settings.XUNFEI_API_KEY,
                    save_folder=file_path,

                )
                logger.info(file_name)
                # 确保文件名不包含路径分隔符
                file_name = os.path.basename(file_name)

                y, sr = librosa.load(os.path.join(file_path ,file_name), sr=None)

                # 计算音频时长（秒）
                duration = librosa.get_duration(y=y, sr=sr)
                duration = round(duration)
                file_path_url = base_url + '/'+file_name
                # duration = question["duration"]
                return {
                    "text": text,
                    "duration": duration,
                    "voiceUrl": file_path_url
                }

        else:
            # 根据历史消息生成回复
            # 这里简单模拟，实际应用中应该调用大模型
            if len(history_messages) > 0:
                last_message = history_messages[-1]
                if last_message["from"] == "user":
                    # 根据用户最后一条消息生成回复
                    user_content = last_message["text"].lower()
                    # messages
                    # prompt_str = messages+ "上面是我们的聊天记录，聊天记录中我的标签是user，你的标签是assistant，请明确区分你我的对话，不要把你的话当成我说的，我是一名大健康行业直销员，你是顾客的角色，通过对我提问和交流，对我不用太客气，锻炼我与客户沟通能力，请你结合历史聊天记录对我提问交流，仅输出下段话就可以，你的话仅仅是对话内容"
                    # robot_words = getds.get_response(prompt_str)

                    chat_msg = getds.get_messages_ai(messages)
                    ddd = datetime.now()
                    robot_words = getds.get_response_qwen(chat_msg)
                    ddd1 = datetime.now()
                    # robot_words1 = getds.get_response(chat_msg)
                    ddd2 = datetime.now()

                    print('1:' + str(ddd1 - ddd))
                    print('1:' + str(ddd2 - ddd1))


                    file_name = text_to_speech(
                        text=robot_words,
                        appid=settings.XUNFEI_APP_ID,
                        apisecret=settings.XUNFEI_API_SECRET,
                        apikey=settings.XUNFEI_API_KEY,
                        save_folder=file_path
                    )
                    # 使用librosa加载音频文件
                    y, sr = librosa.load(os.path.join(file_path ,file_name), sr=None)

                    # 计算音频时长（秒）
                    duration = librosa.get_duration(y=y, sr=sr)
                    duration = round(duration)
                    # 确保文件名不包含路径分隔符
                    file_name = os.path.basename(file_name)
                    file_path_url = base_url + '/' + file_name

                    return {
                        "text": robot_words,
                        "duration": round(int(duration)),
                        "voiceUrl": file_path_url
                    }

    except Exception as e:
        traceback.print_exc()
        logger.error(f"获取机器人消息失败: {str(e)}")
        raise 