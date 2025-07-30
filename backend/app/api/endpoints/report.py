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
from app.db.database import SessionLocal
from app.models.practice import PracticeRecord
from sqlalchemy import desc
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


@router.post("/analyze-organization")
async def analyze_organization(
    request: dict = Body(...),
    token: dict = Depends(get_current_user),
    conversation_service=Depends(get_conversation_service)
):
    try:
        output_path = request.get("output_path")
        practice_id = request.get("practice_id")
        conversation_id = request.get("conversationId")
        user_id = int(token["sub"])  # 转换为整数类型
        
        # 添加调试信息
        logger.info(f"analyze-organization 接收到的参数: practice_id={practice_id}, conversation_id={conversation_id}, user_id={user_id}, output_path={output_path}")
        
        result = await conversation_service.analyze_organization(practice_id,output_path, conversation_id, user_id)
        return {"success": True, "data": result["organization"]}
    except Exception as e:
        logger.error(f"分析组织能力失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-persuasiveness")
async def analyze_persuasiveness(
    request: dict = Body(...),
    token: dict = Depends(get_current_user),
    conversation_service=Depends(get_conversation_service)
):
    try:
        output_path = request.get("output_path")
        practice_id = request.get("practice_id")
        conversation_id = request.get("conversationId")
        user_id = int(token["sub"])  # 转换为整数类型
        result = await conversation_service.analyze_persuasiveness(practice_id,output_path, conversation_id, user_id)
        return {"success": True, "data": result["persuasiveness"]}
    except Exception as e:
        logger.error(f"分析说服力失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-fluency-expression-pronunciation")
async def analyze_fluency_expression_pronunciation(
    request: dict = Body(...),
    token: dict = Depends(get_current_user),
    conversation_service=Depends(get_conversation_service)
):
    try:
        output_path = request.get("output_path")
        practice_id = request.get("practice_id")
        conversation_id = request.get("conversationId")
        user_id = int(token["sub"])  # 转换为整数类型
        result = await conversation_service.analyze_fluency_expression_pronunciation(practice_id, output_path, conversation_id, user_id)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"分析流利度、表达和发音失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/combine-audio")
async def combine_audio(
    request: dict = Body(...),
    token: dict = Depends(get_current_user),
    conversation_service=Depends(get_conversation_service)
):
    try:
        practice_id = request.get("practice_id")
        conversation_id = request.get("conversationId")
        user_id = int(token["sub"])  # 转换为整数类型
        
        # 添加调试信息
        logger.info(f"combine-audio 接收到的参数: practice_id={practice_id}, conversation_id={conversation_id}, user_id={user_id}")
        
        result = await conversation_service.combine_video(practice_id, conversation_id, user_id)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"合并音频失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get-chat-history")
async def get_chat_history(
    request: dict = Body(...),
    token: dict = Depends(get_current_user),
    conversation_service=Depends(get_conversation_service)
):
    """获取练习的对话记录"""
    try:
        practice_id = request.get("practice_id")
        user_id = int(token["sub"])  # 转换为整数类型
        
        # 从数据库获取对话记录
        with SessionLocal() as db:
            practice = db.query(PracticeRecord).filter(
                PracticeRecord.practice_id == practice_id,
                PracticeRecord.is_deleted == 0
            ).first()
            if not practice:
                raise HTTPException(status_code=404, detail="Practice record not found")
            
            # 检查权限 - 确保用户ID类型匹配
            if practice.user_id != user_id:
                logger.error(f"权限验证失败: practice.user_id={practice.user_id}, user_id={user_id}")
                raise HTTPException(status_code=403, detail="Unauthorized access")
            
            # 获取聊天历史
            chat_history = practice.chat_history or []
            
            # 格式化对话记录
            formatted_messages = []
            for msg in chat_history:
                if msg.get("from") and msg.get("text"):
                    formatted_msg = {
                        "from": msg["from"],
                        "text": msg["text"],
                        "timestamp": msg.get("timestamp", ""),
                        "voiceUrl": msg.get("voiceUrl", ""),
                        "duration": msg.get("duration", 3),
                        "suggestion": msg.get("suggestion", "")
                    }
                    formatted_messages.append(formatted_msg)
            
            return {"success": True, "data": formatted_messages}
            
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"用户ID转换失败: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error(f"获取对话记录失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/practice/history")
async def get_practice_history(
    page: int = 1,
    limit: int = 10,
    token: dict = Depends(get_current_user)
):
    """获取用户的练习历史记录"""
    try:
        user_id = int(token["sub"])  # 转换为整数类型
        
        # 从数据库获取练习记录
        with SessionLocal() as db:
            # 计算偏移量
            offset = (page - 1) * limit
            
            # 查询练习记录 - 确保用户ID类型匹配，过滤已删除的记录，并且有聊天记录
            practices = db.query(PracticeRecord).filter(
                PracticeRecord.user_id == user_id,
                PracticeRecord.is_deleted == 0,
                PracticeRecord.chat_history.isnot(None),  # 确保有聊天记录
                PracticeRecord.chat_history != '[]',  # 确保聊天记录不为空数组
                PracticeRecord.chat_history != 'null'  # 确保聊天记录不为null字符串
            ).order_by(desc(PracticeRecord.started_at)).offset(offset).limit(limit).all()
            
            # 格式化练习记录
            formatted_practices = []
            for practice in practices:
                # 检查聊天记录是否包含有效消息
                chat_history = practice.chat_history or []
                if isinstance(chat_history, str):
                    try:
                        chat_history = json.loads(chat_history)
                    except (json.JSONDecodeError, TypeError):
                        chat_history = []
                
                # 过滤出有效的消息（有from和text字段）
                valid_messages = []
                if isinstance(chat_history, list):
                    for msg in chat_history:
                        if isinstance(msg, dict) and msg.get("from") and msg.get("text"):
                            valid_messages.append(msg)
                
                # 如果没有有效消息，跳过这个练习记录
                if not valid_messages:
                    continue
                
                # 解析评分数据 - 使用新的独立字段
                organization_score = 0
                persuasiveness_score = 0
                fluency_score = 0
                pronunciation_score = 0
                expression_score = 0
                score_json = {}  # 初始化score_json变量
                
                # 从独立字段获取数据
                if practice.organization_score:
                    organization_score = practice.organization_score.get("score", 0)
                
                if practice.persuasiveness_score:
                    persuasiveness_score = practice.persuasiveness_score.get("score", 0)
                
                if practice.fluency_pronunciation_expression_score:
                    fluency_score = practice.fluency_pronunciation_expression_score.get("fluency", {}).get("score", 0)
                    pronunciation_score = practice.fluency_pronunciation_expression_score.get("pronunciation", {}).get("score", 0)
                    expression_score = practice.fluency_pronunciation_expression_score.get("expression", {}).get("score", 0)
                
                # 如果没有独立字段数据，尝试从旧的score_json获取
                if not any([organization_score, persuasiveness_score, fluency_score, pronunciation_score, expression_score]):
                    score_json = practice.score_json or {}
                    organization_score = score_json.get("organization", {}).get("score", 0)
                    persuasiveness_score = score_json.get("persuasiveness", {}).get("score", 0)
                    fluency_score = score_json.get("fluency", {}).get("score", 0)
                    pronunciation_score = score_json.get("pronunciation", {}).get("score", 0)
                    expression_score = score_json.get("expression", {}).get("score", 0)
                
                # 判断是否有分析报告
                has_report = bool(any([
                    organization_score > 0,
                    persuasiveness_score > 0,
                    fluency_score > 0,
                    pronunciation_score > 0,
                    expression_score > 0
                ]))
                
                # 计算总体评分
                scores = [organization_score, persuasiveness_score, fluency_score, pronunciation_score, expression_score]
                overall_score = round(sum(scores) / len(scores)) if scores and any(scores) else 0
                
                # 获取场景名称
                scene_names = {
                    0: '核苷酸介绍',
                    1: '新客户开发',
                    2: '异议处理',
                    3: '产品推荐',
                    4: '成交技巧'
                }
                scene_name = scene_names.get(practice.scenario_id, '未知场景')
                
                # 获取状态文本
                status_texts = {
                    'in_progress': '进行中',
                    'completed': '已完成',
                    'paused': '已暂停',
                    'cancelled': '已取消'
                }
                status_text = status_texts.get(practice.status, '未知状态')
                
                formatted_practice = {
                    "practiceId": practice.practice_id,
                    "conversationId": practice.conversation_id or '',
                    "sceneId": practice.scenario_id,
                    "sceneName": scene_name,
                    "overallScore": overall_score,
                    "organizationScore": organization_score,
                    "persuasivenessScore": persuasiveness_score,
                    "fluencyScore": fluency_score,
                    "pronunciationScore": pronunciation_score,
                    "expressionScore": expression_score,
                    "createdAt": practice.started_at.strftime("%Y-%m-%d %H:%M") if practice.started_at else "",
                    "status": practice.status,
                    "statusText": status_text,
                    "hasReport": has_report,
                    "messageCount": len(valid_messages)  # 添加消息数量
                }
                formatted_practices.append(formatted_practice)
            
            return {"success": True, "data": {"practices": formatted_practices}}
            
    except ValueError as e:
        logger.error(f"用户ID转换失败: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error(f"获取练习历史失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-report/{practice_id}")
async def get_report_data(
    practice_id: int,
    token: dict = Depends(get_current_user)
):
    try:
        user_id = int(token["sub"])
        
        with SessionLocal() as db:
            practice = db.query(PracticeRecord).filter(
                PracticeRecord.practice_id == practice_id,
                PracticeRecord.user_id == user_id,
                PracticeRecord.is_deleted == 0
            ).first()
            
            if not practice:
                raise HTTPException(status_code=404, detail="Practice record not found")
            
            # 从独立字段构建score_json
            score_json = {}
            
            if practice.organization_score:
                score_json["organization"] = practice.organization_score
            
            if practice.persuasiveness_score:
                score_json["persuasiveness"] = practice.persuasiveness_score
            
            if practice.fluency_pronunciation_expression_score:
                score_json.update(practice.fluency_pronunciation_expression_score)
            
            # 如果没有独立字段数据，尝试从旧的score_json获取
            if not score_json and practice.score_json:
                score_json = practice.score_json
            
            return {
                "success": True,
                "data": {
                    "practice_id": practice.practice_id,
                    "scores": score_json
                }
            }
            
    except Exception as e:
        logger.error(f"获取报告数据失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/practice/{practice_id}")
async def delete_practice_record(
    practice_id: int,
    token: dict = Depends(get_current_user)
):
    """逻辑删除练习记录"""
    try:
        user_id = int(token["sub"])
        
        with SessionLocal() as db:
            practice = db.query(PracticeRecord).filter(
                PracticeRecord.practice_id == practice_id,
                PracticeRecord.user_id == user_id,
                PracticeRecord.is_deleted == 0
            ).first()
            
            if not practice:
                raise HTTPException(status_code=404, detail="练习记录不存在或已被删除")
            
            # 逻辑删除：将 is_deleted 设置为 1
            practice.is_deleted = 1
            db.commit()
            
            return {"success": True, "message": "练习记录已删除"}
            
    except ValueError as e:
        logger.error(f"用户ID转换失败: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid user ID")
    except Exception as e:
        logger.error(f"删除练习记录失败: {str(e)}")
        traceback.print_exc()