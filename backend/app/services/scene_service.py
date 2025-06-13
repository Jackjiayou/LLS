from typing import Optional, Dict, Any
import random
from ..models.scene import scenes, questions
from ..core.logging import logger

def get_scene(scene_id: int) -> Optional[Dict[str, Any]]:
    """
    获取指定场景的详细信息
    """
    try:
        return next((s for s in scenes if s["id"] == scene_id), None)
    except Exception as e:
        logger.error(f"获取场景信息失败: {str(e)}")
        return None

def get_random_question(scene_id: int) -> Optional[Dict[str, Any]]:
    """
    获取指定场景的随机问题
    """
    try:
        if scene_id not in questions:
            return None
        
        scene_questions = questions[scene_id]
        if not scene_questions:
            return None
        
        return random.choice(scene_questions)
    except Exception as e:
        logger.error(f"获取随机问题失败: {str(e)}")
        return None

def get_scene_questions(scene_id: int) -> list:
    """
    获取指定场景的所有问题
    """
    try:
        return questions.get(scene_id, [])
    except Exception as e:
        logger.error(f"获取场景问题列表失败: {str(e)}")
        return [] 