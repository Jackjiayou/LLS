from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from datetime import datetime, timedelta
from typing import List, Optional
import json

from app.db.database import get_db
from app.models.practice import PracticeRecord, PracticeScenario
from app.models.user import User
from app.core.auth import get_current_user
from app.schemas.ranking import RankingResponse, RankingItem, CurrentUserRank

router = APIRouter()

@router.get("/ranking/list", response_model=RankingResponse)
async def get_ranking_list(
    time_period: str = Query("today", description="时间周期: today, week, month, all"),
    scenario_id: str = Query("all", description="场景ID: all 或具体场景ID"),
    sort_by: str = Query("avg_score", description="排序方式: avg_score, max_score, total_score, duration"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取排行榜数据
    """
    try:
        # 获取当前用户ID
        current_user_id = current_user.get("sub")
        
        # 构建时间过滤条件
        now = datetime.utcnow()
        if time_period == "today":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "week":
            start_time = now - timedelta(days=now.weekday())
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "month":
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # all
            start_time = None
        
        # 获取所有练习记录
        query = db.query(PracticeRecord).filter(PracticeRecord.is_deleted == 0)
        
        # 添加时间过滤
        if start_time:
            query = query.filter(PracticeRecord.started_at >= start_time)
        
        # 添加场景过滤
        if scenario_id != "all":
            query = query.filter(PracticeRecord.scenario_id == int(scenario_id))
        
        records = query.all()
        
        # 按用户分组计算统计数据
        user_stats = {}
        
        for record in records:
            user_id = record.user_id
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'practice_count': 0,
                    'total_duration': 0,
                    'scenarios': set(),
                    'completed_scenarios': set(),  # 完成的场景
                    'scores': []
                }
            
            user_stats[user_id]['practice_count'] += 1
            user_stats[user_id]['scenarios'].add(record.scenario_id)
            
            # 如果练习已完成且有分数，算作完成的场景
            if record.status == 'completed':
                # 检查是否有分数（从新的分数字段）
                has_score = False
                
                # 检查组织能力分数
                if record.organization_score:
                    try:
                        if isinstance(record.organization_score, dict) and record.organization_score.get('score', 0) > 0:
                            has_score = True
                    except:
                        pass
                
                # 检查说服力分数
                if not has_score and record.persuasiveness_score:
                    try:
                        if isinstance(record.persuasiveness_score, dict) and record.persuasiveness_score.get('score', 0) > 0:
                            has_score = True
                    except:
                        pass
                
                # 检查流利度、发音、表达分数
                if not has_score and record.fluency_pronunciation_expression_score:
                    try:
                        if isinstance(record.fluency_pronunciation_expression_score, dict):
                            fluency_score = record.fluency_pronunciation_expression_score.get('fluency', {}).get('score', 0)
                            pronunciation_score = record.fluency_pronunciation_expression_score.get('pronunciation', {}).get('score', 0)
                            expression_score = record.fluency_pronunciation_expression_score.get('expression', {}).get('score', 0)
                            
                            if fluency_score > 0 or pronunciation_score > 0 or expression_score > 0:
                                has_score = True
                    except:
                        pass
                
                if has_score:
                    user_stats[user_id]['completed_scenarios'].add(record.scenario_id)
            
            # 计算练习时长
            if record.started_at and record.ended_at:
                duration = (record.ended_at - record.started_at).total_seconds() / 3600
                user_stats[user_id]['total_duration'] += duration
            
            # 只有完成的练习才计算分数
            if record.status == 'completed':
                total_score = 0
                count = 0
                
                # 组织能力分数
                if record.organization_score:
                    try:
                        if isinstance(record.organization_score, dict):
                            org_score = record.organization_score.get('score', 0)
                            if org_score > 0:
                                total_score += org_score
                                count += 1
                    except:
                        pass
                
                # 说服力分数
                if record.persuasiveness_score:
                    try:
                        if isinstance(record.persuasiveness_score, dict):
                            per_score = record.persuasiveness_score.get('score', 0)
                            if per_score > 0:
                                total_score += per_score
                                count += 1
                    except:
                        pass
                
                # 流利度、发音、表达分数
                if record.fluency_pronunciation_expression_score:
                    try:
                        if isinstance(record.fluency_pronunciation_expression_score, dict):
                            fluency_score = record.fluency_pronunciation_expression_score.get('fluency', {}).get('score', 0)
                            pronunciation_score = record.fluency_pronunciation_expression_score.get('pronunciation', {}).get('score', 0)
                            expression_score = record.fluency_pronunciation_expression_score.get('expression', {}).get('score', 0)
                            
                            if fluency_score > 0:
                                total_score += fluency_score
                                count += 1
                            if pronunciation_score > 0:
                                total_score += pronunciation_score
                                count += 1
                            if expression_score > 0:
                                total_score += expression_score
                                count += 1
                    except:
                        pass
                
                # 计算平均分数
                if count > 0:
                    avg_score = total_score / count
                    user_stats[user_id]['scores'].append(avg_score)
        
        # 计算每个用户的平均分数
        user_rankings = []
        for user_id, stats in user_stats.items():
            avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
            
            user_rankings.append({
                'user_id': user_id,
                'practice_count': stats['practice_count'],
                'total_duration': stats['total_duration'],
                'scenario_count': len(stats['completed_scenarios']),  # 使用完成的场景数量
                'avg_score': avg_score,
                'scores': stats['scores']  # 添加scores字段用于排序
            })
        
        # 根据排序方式排序
        if sort_by == "duration":
            user_rankings.sort(key=lambda x: x['total_duration'], reverse=True)
            score_field = 'total_duration'
        elif sort_by == "max_score":
            # 按最高分排序
            for item in user_rankings:
                item['max_score'] = max(item['scores']) if item['scores'] else 0
            user_rankings.sort(key=lambda x: x['max_score'], reverse=True)
            score_field = 'max_score'
        elif sort_by == "total_score":
            # 按总分排序
            for item in user_rankings:
                item['total_score'] = sum(item['scores']) if item['scores'] else 0
            user_rankings.sort(key=lambda x: x['total_score'], reverse=True)
            score_field = 'total_score'
        else:  # avg_score (默认)
            user_rankings.sort(key=lambda x: x['avg_score'], reverse=True)
            score_field = 'avg_score'
        
        # 获取用户信息
        user_ids = [item['user_id'] for item in user_rankings]
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        user_dict = {user.id: user for user in users}
        
        # 构建排行榜列表
        ranking_list = []
        for i, item in enumerate(user_rankings):
            user = user_dict.get(item['user_id'])
            if user:
                ranking_list.append(RankingItem(
                    user_id=user.id,
                    name=user.nickname or "用户" + str(user.id),
                    avatar=user.avatar_url,
                    score=round(item[score_field], 1),
                    scenario_count=item['scenario_count']
                ))
        
        # 获取当前用户排名
        current_user_rank = None
        for i, item in enumerate(ranking_list):
            if item.user_id == current_user_id:
                current_user_rank = CurrentUserRank(
                    user_id=item.user_id,
                    name=item.name,
                    avatar=item.avatar,
                    score=item.score,
                    scenario_count=item.scenario_count,
                    rank=i + 1
                )
                break
        
        return RankingResponse(
            ranking_list=ranking_list,
            current_user=current_user_rank
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取排行榜数据失败: {str(e)}") 