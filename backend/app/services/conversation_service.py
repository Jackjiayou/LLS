from datetime import datetime
import uuid
from typing import List, Optional, Dict, Any
import json
import random
import logging
import os
import  asyncio
from app.utils.xfyun_asr import  run_xfyun_asr
from app.utils.data import request_data, APPId, APIKey, APISecret, request_url
from sqlalchemy import func
import traceback
import librosa
from app.models.conversation import Conversation, Message
from app.core.config import settings
from app.utils import getds,combined_audio
from app.models import scene
from app.utils.personification_text_to_speach import text_to_speech
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
import  numpy as np

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

    async def combine_video(self, practice_id: int, conversation_id: str, user_id: str):
        try:
            # 添加调试信息
            logger.info(f"combine_video 接收到的参数: practice_id={practice_id}, conversation_id={conversation_id}, user_id={user_id}")
            with SessionLocal() as db:
                practice = db.query(PracticeRecord).filter(PracticeRecord.practice_id == practice_id).first()
                # practice_id = 183  # todo
                # conversation_id = '97b38417-2bc8-4d2d-9183-f5d2e0a0108f'  # todo
                conversation_id = practice.conversation_id
                audio_path = os.path.join(settings.file_path_voice, str(user_id), conversation_id)
                os.makedirs(audio_path, exist_ok=True)
                file_name = f'{conversation_id}_combine.mp3'
                output_path = os.path.join(audio_path, file_name)
                file_path = combined_audio.combine_audios_in_folder(audio_path, output_path)

            return file_path
        except Exception as e:
            logger.error(f"combine_video失败: {str(e)}")
            traceback.print_exc()

            return ''

    def _update_score_json_atomic(self, practice_id: int, updates: dict) -> None:
        """
        原子性地更新score_json，避免并发问题
        使用重试机制来处理并发冲突
        """
        import time
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with SessionLocal() as db:
                    # 获取最新的practice记录
                    practice = db.query(PracticeRecord).filter(
                        PracticeRecord.practice_id == practice_id
                    ).first()
                    
                    if not practice:
                        raise ValueError(f"Practice record not found: {practice_id}")
                    
                    # 获取现有的score_json，如果不存在则创建新的
                    existing_score_json = practice.score_json or {}
                    
                    # 应用更新
                    existing_score_json.update(updates)
                    
                    # 存储到practice
                    practice.score_json = existing_score_json
                    db.commit()
                    
                    logger.info(f"原子更新score_json完成 - practice_id: {practice_id}, 更新: {list(updates.keys())}")
                    return
                    
            except Exception as e:
                retry_count += 1
                logger.warning(f"更新score_json失败，重试 {retry_count}/{max_retries}: {str(e)}")
                if retry_count >= max_retries:
                    logger.error(f"更新score_json最终失败: {str(e)}")
                    raise
                time.sleep(0.1 * retry_count)  # 指数退避

    async def analyze_persuasiveness(self, practice_id: int,output_path :str, conversation_id: str, user_id: str) -> dict:
        """
        对练习进行分析打分，返回各项分数和分析文本
        """
        # 添加调试信息
        logger.info(f"analyze_persuasiveness 接收到的参数: practice_id={practice_id}, conversation_id={conversation_id}, user_id={user_id}, output_path={output_path}")
        
        # practice_id = 183  # todo
        # conversation_id = '97b38417-2bc8-4d2d-9183-f5d2e0a0108f'  # todo
        try:
            with SessionLocal() as db:
                practice = db.query(PracticeRecord).filter(PracticeRecord.practice_id == practice_id).first()
                if not practice:
                    raise ValueError(f"Practice record not found: {practice_id}")

                # 1. 获取聊天历史
                chat_history = practice.chat_history or []

                dialogue_for_llm = [
                    {"from": msg.get("from"), "text": msg.get("text"), "suggestion": msg.get("suggestion")}
                    for msg in chat_history if msg.get("from") and msg.get("text")
                ]
                dialogue_str = "\n".join([f"{msg['from']}: {msg['text']}" + (f" (建议: {msg['suggestion']})" if msg.get('suggestion') else "") for msg in dialogue_for_llm])


                # 2. 语言组织能力、说服力（大模型分析，伪代码/接口）
                # 可以用OpenAI、Qwen等大模型API
                def call_llm_for_ability(texts, ability_type):
                    import re
                    # ability_type: "organization" or "persuasiveness"
                    # 伪代码：实际用模型API
                    # 构建系统消息（包含角色定义和规则）
                    if ability_type == "说服力":
                        prompt = "请对以下用户（user）与客户（customer）的对话内容的说服力进行1-100分打分和分析。\n\n" + \
                                 "评分标准：\n" + \
                                 "- 90-100分：极具说服力，能有效引导客户决策\n" + \
                                 "- 80-89分：说服力较强，表达清晰有效\n" + \
                                 "- 70-79分：说服力一般，基本能表达观点\n" + \
                                 "- 60-69分：说服力较弱，缺乏说服技巧\n" + \
                                 "- 60分以下：说服力很差，无法有效沟通\n\n" + \
                                 "分析要点：\n" + \
                                 "1. 是否有效识别并回应客户需求\n" + \
                                 "2. 是否提供有力的论据和案例\n" + \
                                 "3. 是否运用了合适的说服技巧\n" + \
                                 "4. 是否处理了客户异议\n" + \
                                 "5. 是否建立了信任关系\n\n" + \
                                 "注意：括号中的内容是对用户回答的改进建议和示例，是更好的回答方式。请对比用户（user）实际回答与建议的改进方案以及结合客户（customer）的问题来评价说服力。\n\n" + \
                                 "对话记录：\n" + texts + "\n\n" + \
                                 '请输出JSON格式：{"score": 分数, "analysis": "详细分析"}'
                    elif ability_type == "语言组织能力":
                        prompt = f"""请对以下用户（user）与客户（customer）的对话内容的语言组织能力进行1-100分打分和分析。

                                    评分标准：
                                    - 90-100分：语言组织极佳，结构清晰，逻辑严密
                                    - 80-89分：语言组织良好，结构清晰，逻辑合理
                                    - 70-79分：语言组织一般，基本清晰，偶有混乱
                                    - 60-69分：语言组织较弱，结构不够清晰
                                    - 60分以下：语言组织很差，结构混乱
                                    
                                    分析要点：
                                    1. 语言结构是否清晰有序
                                    2. 逻辑层次是否分明
                                    3. 表达是否简洁明了
                                    4. 是否有效运用过渡词
                                    5. 是否避免了重复和冗余
                                    
                                    注意：括号中的内容是对用户回答的改进建议和示例，是更好的回答方式。请对比用户（user）实际回答与建议的改进方案以及结合客户（customer）的问题来评价语言组织能力。
                                    
                                    对话记录：
                                    {texts}
                                    
                                    请输出JSON格式：{{"score": 分数, "analysis": "详细分析"}}"""

                    system_message = {
                        'role': 'system',
                        'content': prompt
                    }

                    messages = [system_message]
                    str_reslt = getds.get_response_qwen(messages)

                    # 1. 尝试提取 {...} 之间的内容
                    match = re.search(r'\{.*?\}', str_reslt, re.DOTALL)
                    if match:
                        json_str = match.group(0)
                        try:
                            result = json.loads(json_str)
                            return result['score'], result['analysis']
                        except Exception as e:
                            print("JSON解析失败:", e, json_str)
                    # 2. 尝试提取 score: xx analysis: ...
                    match2 = re.search(r'score[:：]\s*(\d+)[,， ]*analysis[:：]?\s*(.*)', str_reslt, re.IGNORECASE|re.DOTALL)
                    if match2:
                        score = int(match2.group(1))
                        analysis = match2.group(2).strip()
                        return score, analysis
                    # 3. 兜底
                    print("大模型返回格式无法解析:", str_reslt)
                    return 0, "大模型返回格式错误"


                pers_score, pers_analysis = call_llm_for_ability(dialogue_str, "说服力")

                # 5. 直接保存到独立字段，避免并发问题
                logger.info(f"准备更新说服力数据 - 分数: {pers_score}, 分析: {pers_analysis[:50]}...")
                with SessionLocal() as db:
                    practice = db.query(PracticeRecord).filter(PracticeRecord.practice_id == practice_id).first()
                    if practice:
                        practice.persuasiveness_score = {"score": pers_score, "analysis": pers_analysis}
                        db.commit()
                        logger.info(f"说服力数据保存成功 - practice_id: {practice_id}")
                    else:
                        logger.error(f"Practice record not found: {practice_id}")
                
                # 添加调试信息
                logger.info(f"说服力分析完成 - 分数: {pers_score}, 分析: {pers_analysis[:100]}...")

                return {"persuasiveness": {"score": pers_score, "analysis": pers_analysis}}
        except Exception as e:
            logger.error(f"开始练习失败: {str(e)}")
            traceback.print_exc()
            return {"persuasiveness": {"score": 0, "analysis": "分析失败"}}

    async def analyze_organization(self, practice_id: int, output_path: str, conversation_id: str,
                                                  user_id: str) -> dict:
        """
        对练习进行分析打分，返回各项分数和分析文本
        """
        # 添加调试信息
        logger.info(f"analyze_organization 接收到的参数: practice_id={practice_id}, conversation_id={conversation_id}, user_id={user_id}, output_path={output_path}")
        
        # practice_id = 183  # todo
        # conversation_id = '97b38417-2bc8-4d2d-9183-f5d2e0a0108f'  # todo
        try:
            with SessionLocal() as db:
                practice = db.query(PracticeRecord).filter(PracticeRecord.practice_id == practice_id).first()
                if not practice:
                    raise ValueError(f"Practice record not found: {practice_id}")

                # 1. 获取聊天历史
                chat_history = practice.chat_history or []

                dialogue_for_llm = [
                    {"from": msg.get("from"), "text": msg.get("text"), "suggestion": msg.get("suggestion")}
                    for msg in chat_history if msg.get("from") and msg.get("text")
                ]
                dialogue_str = "\n".join([f"{msg['from']}: {msg['text']}" + (
                    f" (建议: {msg['suggestion']})" if msg.get('suggestion') else "") for msg in dialogue_for_llm])

                # 2. 语言组织能力、说服力（大模型分析，伪代码/接口）
                # 可以用OpenAI、Qwen等大模型API
                def call_llm_for_ability(texts, ability_type):
                    import re
                    # ability_type: "organization" or "persuasiveness"
                    # 伪代码：实际用模型API
                    # 构建系统消息（包含角色定义和规则）
                    if ability_type == "说服力":
                        prompt = "请对以下用户（user）与客户（customer）的对话内容的说服力进行1-100分打分和分析。\n\n" + \
                                 "评分标准：\n" + \
                                 "- 90-100分：极具说服力，能有效引导客户决策\n" + \
                                 "- 80-89分：说服力较强，表达清晰有效\n" + \
                                 "- 70-79分：说服力一般，基本能表达观点\n" + \
                                 "- 60-69分：说服力较弱，缺乏说服技巧\n" + \
                                 "- 60分以下：说服力很差，无法有效沟通\n\n" + \
                                 "分析要点：\n" + \
                                 "1. 是否有效识别并回应客户需求\n" + \
                                 "2. 是否提供有力的论据和案例\n" + \
                                 "3. 是否运用了合适的说服技巧\n" + \
                                 "4. 是否处理了客户异议\n" + \
                                 "5. 是否建立了信任关系\n\n" + \
                                 "注意：括号中的内容是对用户回答的改进建议和示例，是更好的回答方式。请对比用户（user）实际回答与建议的改进方案以及结合客户（customer）的问题来评价说服力。\n\n" + \
                                 "对话记录：\n" + texts + "\n\n" + \
                                 '请输出JSON格式：{"score": 分数, "analysis": "详细分析"}'
                    elif ability_type == "语言组织能力":
                        prompt = f"""请对以下用户（user）与客户（customer）的对话内容的语言组织能力进行1-100分打分和分析。

                                     评分标准：
                                     - 90-100分：语言组织极佳，结构清晰，逻辑严密
                                     - 80-89分：语言组织良好，结构清晰，逻辑合理
                                     - 70-79分：语言组织一般，基本清晰，偶有混乱
                                     - 60-69分：语言组织较弱，结构不够清晰
                                     - 60分以下：语言组织很差，结构混乱

                                     分析要点：
                                     1. 语言结构是否清晰有序
                                     2. 逻辑层次是否分明
                                     3. 表达是否简洁明了
                                     4. 是否有效运用过渡词
                                     5. 是否避免了重复和冗余

                                     注意：括号中的内容是对用户回答的改进建议和示例，是更好的回答方式。请对比用户（user）实际回答与建议的改进方案以及结合客户（customer）的问题来评价语言组织能力。

                                     对话记录：
                                     {texts}

                                     请输出JSON格式：{{"score": 分数, "analysis": "详细分析"}}"""

                    system_message = {
                        'role': 'system',
                        'content': prompt
                    }

                    messages = [system_message]
                    str_reslt = getds.get_response_qwen(messages)

                    # 1. 尝试提取 {...} 之间的内容
                    match = re.search(r'\{.*?\}', str_reslt, re.DOTALL)
                    if match:
                        json_str = match.group(0)
                        try:
                            result = json.loads(json_str)
                            return result['score'], result['analysis']
                        except Exception as e:
                            print("JSON解析失败:", e, json_str)
                    # 2. 尝试提取 score: xx analysis: ...
                    match2 = re.search(r'score[:：]\s*(\d+)[,， ]*analysis[:：]?\s*(.*)', str_reslt,
                                       re.IGNORECASE | re.DOTALL)
                    if match2:
                        score = int(match2.group(1))
                        analysis = match2.group(2).strip()
                        return score, analysis
                    # 3. 兜底
                    print("大模型返回格式无法解析:", str_reslt)
                    return 0, "大模型返回格式错误"

                org_score, org_analysis = call_llm_for_ability(dialogue_str, "语言组织能力")

                # 5. 直接保存到独立字段，避免并发问题
                logger.info(f"准备更新语言组织能力数据 - 分数: {org_score}, 分析: {org_analysis[:50]}...")
                with SessionLocal() as db:
                    practice = db.query(PracticeRecord).filter(PracticeRecord.practice_id == practice_id).first()
                    if practice:
                        practice.organization_score = {"score": org_score, "analysis": org_analysis}
                        db.commit()
                        logger.info(f"语言组织能力数据保存成功 - practice_id: {practice_id}")
                    else:
                        logger.error(f"Practice record not found: {practice_id}")
                
                # 添加调试信息
                logger.info(f"语言组织能力分析完成 - 分数: {org_score}, 分析: {org_analysis[:100]}...")

                return {"organization": {"score": org_score, "analysis": org_analysis}}
        except Exception as e:
            logger.error(f"分析语言组织能力失败: {str(e)}")
            traceback.print_exc()
            return {"organization": {"score": 0, "analysis": "分析失败"}}

    async def analyze_fluency_expression_pronunciation(self, practice_id: int, output_path: str, conversation_id: str, user_id: str) -> dict:
        """
        对练习进行分析打分，返回各项分数和分析文本
        """
        # 添加调试信息
        logger.info(f"analyze_fluency_expression_pronunciation 接收到的参数: practice_id={practice_id}, conversation_id={conversation_id}, user_id={user_id}, output_path={output_path}")

        try:
            # practice_id = 183  # todo
            # conversation_id = '97b38417-2bc8-4d2d-9183-f5d2e0a0108f'  # todo



            with SessionLocal() as db:
                practice = db.query(PracticeRecord).filter(PracticeRecord.practice_id == practice_id).first()
                if not practice:
                    raise ValueError(f"Practice record not found: {practice_id}")
                conversation_id = practice.conversation_id
                audio_path = os.path.join(settings.file_path_voice, str(user_id), practice.conversation_id)
                file_name = f'{conversation_id}_combine.mp3'
                output_path = os.path.join(audio_path, file_name)

                # 1. 获取聊天历史
                chat_history = practice.chat_history or []

                user_texts = [msg['text'] for msg in chat_history if msg.get('from') == 'user']
                user_voice_urls = [msg['voiceUrl'] for msg in chat_history if
                                   msg.get('from') == 'user' and msg.get('voiceUrl')]
                user_texts_str = ','.join(user_texts)

                import copy
                req_data = copy.deepcopy(request_data)
                # 假设音频路径字段为 payload->data->audio

                req_data["parameter"]["st"]["refText"] = user_texts_str
                req_data["payload"]["data"]["audio"] = output_path
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    run_xfyun_asr,
                    req_data, APPId, APIKey, APISecret, request_url
                )
                json_result = json.loads(result)['result']
                dialogue_for_llm = [
                    {"from": msg.get("from"), "text": msg.get("text"), "suggestion": msg.get("suggestion")}
                    for msg in chat_history if msg.get("from") and msg.get("text")
                ]
                dialogue_str = "\n".join([f"{msg['from']}: {msg['text']}" + (f" (建议: {msg['suggestion']})" if msg.get('suggestion') else "") for msg in dialogue_for_llm])



                # 3. 流利度（可直接实现：如平均语速、停顿等，简单实现如下）
                def calc_fluency(json_result):
                    speed = int(json_result['speed'])
                    # 简单实现：平均句长/字数，越高越流利
                    if not speed:
                        return 60, "无有效语音"

                    # score = min(100, max(60, int(avg_len * 2)))
                    score = json_result['fluency']
                    analysis = f"流利度得分{score},{evaluate_speed(speed)}"

                    return score, analysis

                def evaluate_speed(avg_speed):
                    if avg_speed < 120:
                        return f"语速为{avg_speed:.1f}字/分钟，语速偏慢，建议适当加快。"
                    elif avg_speed < 160:
                        return f"语速为{avg_speed:.1f}字/分钟，稍慢，适合初学者或强调。"
                    elif avg_speed < 220:
                        return f"语速为{avg_speed:.1f}字/分钟，正常、自然、易于理解。"
                    elif avg_speed < 260:
                        return f"语速为{avg_speed:.1f}字/分钟，稍快，注意听众理解。"
                    else:
                        return f"语速为{avg_speed:.1f}字/分钟，语速偏快，建议放慢。"

                def evaluate_rhythm(rhythm_score):
                    """
                    根据韵律度得分给出评价建议
                    :param rhythm_score: int, 0-100
                    :return: str
                    """
                    if rhythm_score < 60:
                        return f"韵律度得分为{rhythm_score}，语音表达较为平淡，缺乏情感起伏，建议加强语调变化，提升表达感染力。"
                    elif rhythm_score < 75:
                        return f"韵律度得分为{rhythm_score}，语音表达基本自然，但情感色彩略显不足，可适当增加语调变化，使表达更生动。"
                    elif rhythm_score < 90:
                        return f"韵律度得分为{rhythm_score}，语音表达较为自然，情感传递较好，建议继续保持并适当丰富语音表现力。"
                    else:
                        return f"韵律度得分为{rhythm_score}，语音表达非常自然，情感丰富，富有感染力，表现优秀！"

                # 4. 发音准确度、语音表达（伪代码/接口）

                def calc_pronunciation(voice_urls):

                    pronunciation_score = json_result['pronunciation']
                    pronunciation_analysis = evaluate_pronunciation(pronunciation_score)
                    # result = call_speech_eval_api(voice_urls)
                    # return result['score'], result['analysis']

                    return pronunciation_score, pronunciation_analysis

                def calc_expression(json_result):
                    expression_score = json_result['rhythm']
                    expression_analysis = evaluate_rhythm(expression_score)
                    return expression_score, expression_analysis

                fluency_score, fluency_analysis = calc_fluency(json_result)

                pronunciation_score, pronunciation_analysis = calc_pronunciation(json_result)
                expression_score, expression_analysis = calc_expression(json_result)

                # 5. 直接保存到独立字段，避免并发问题
                logger.info(f"准备更新流利度等数据 - fluency: {fluency_score}, pronunciation: {pronunciation_score}, expression: {expression_score}")
                with SessionLocal() as db:
                    practice = db.query(PracticeRecord).filter(PracticeRecord.practice_id == practice_id).first()
                    if practice:
                        practice.fluency_pronunciation_expression_score = {
                            "fluency": {"score": fluency_score, "analysis": fluency_analysis},
                            "pronunciation": {"score": pronunciation_score, "analysis": pronunciation_analysis},
                            "expression": {"score": expression_score, "analysis": expression_analysis}
                        }
                        db.commit()
                        logger.info(f"流利度等数据保存成功 - practice_id: {practice_id}")
                    else:
                        logger.error(f"Practice record not found: {practice_id}")

                return {
                    "fluency": {"score": fluency_score, "analysis": fluency_analysis},
                    "pronunciation": {"score": pronunciation_score, "analysis": pronunciation_analysis},
                    "expression": {"score": expression_score, "analysis": expression_analysis}
                }
        except Exception as e:
            logger.error(f"分析流利度、发音、表达失败: {str(e)}")
            traceback.print_exc()
            return {
                "fluency": {"score": 0, "analysis": "分析失败"},
                "pronunciation": {"score": 0, "analysis": "分析失败"},
                "expression": {"score": 0, "analysis": "分析失败"}
            }

    async def start_practice(self, user_id: int, scenario_id: int, conversation_id: str = None) -> Dict[str, Any]:
        """开始新的练习"""
        try:
            with SessionLocal() as db:
                practice = PracticeRecord(
                    user_id=user_id,
                    scenario_id=scenario_id,
                    status='in_progress',
                    conversation_id=conversation_id  # 保存 conversation_id
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

    async def save_json_message(self, practice_id: int, messages: List[Dict[str, Any]], conversation_id: str = None) -> None:
        """保存聊天记录"""
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

                practice.status = 'completed'
                practice.ended_at = datetime.utcnow()
                practice.chat_history = message_list
                practice.updated_at = datetime.utcnow()
                
                # 保存 conversation_id
                if conversation_id:
                    practice.conversation_id = conversation_id

                # 提交更改
                db.commit()

            logger.info(f"Successfully saved chat history for practice {practice_id} with conversation_id {conversation_id}")
        except Exception as e:
            traceback.print_exc()
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
            db_path = settings.vec_db_production if scene_id == 0 else settings.vec_db_nucleotide

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

            # 极速版 todo
            new_name = convert_mp3_16k(local_url)
            os.remove(local_url)
            os.rename(local_url.replace( '.mp3','_16k.mp3'),file_location)
            #new_local_url = file_location.replace('.mp3', '_16k.mp3')
           # new_url = os.path.join(paths["voice_path"], new_name)



            str_result = st(local_url, settings.XUNFEI_APP_ID, settings.XUNFEI_API_KEY, settings.XUNFEI_API_SECRET)
            str_result = extract_words_from_lattice2(str_result)

            return {"text": str_result, "voiceUrl": voice_url}

        except Exception as e:
            logger.error(traceback.format_exc())
            traceback.print_exc()
            raise Exception(f"上传文件处理失败: {str(e)}")

def evaluate_pronunciation(pronunciation_score):
    """
    根据发音准确度得分给出评价建议
    :param pronunciation_score: int, 0-100
    :return: str
    """
    if pronunciation_score < 60:
        return f"发音准确度得分为{pronunciation_score}，发音存在较多错误，建议加强音标和单词发音的练习，注意模仿标准发音。"
    elif pronunciation_score < 75:
        return f"发音准确度得分为{pronunciation_score}，发音基本准确，但仍有部分单词或音节发音不清晰，建议有针对性地纠正易错音。"
    elif pronunciation_score < 90:
        return f"发音准确度得分为{pronunciation_score}，发音较为标准，偶有小瑕疵，建议继续保持并进一步提升发音细节。"
    else:
        return f"发音准确度得分为{pronunciation_score}，发音非常标准清晰，几乎无可挑剔，表现优秀！"

# 新增依赖注入工厂
def get_conversation_service():
    return ConversationService()

