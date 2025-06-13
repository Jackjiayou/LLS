import os
import json
from datetime import datetime
import random
from ..utils.audio import convert_mp3_16k
from ..utils.personification_text_to_speach import text_to_speech as tts
from app.core.logger import logger, log_request, log_response, log_error

def extract_words_from_lattice2(data):
    """提取lattice2中的文字内容并按时间顺序拼接"""
    # 获取所有段落并按开始时间排序
    segments = sorted(data['lattice2'], key=lambda x: int(x['begin']))

    text_parts = []
    for seg in segments:
        words = []
        # 遍历语音识别结果的多层结构
        for rt in seg['json_1best']['st']['rt']:
            for ws in rt['ws']:
                for cw in ws['cw']:
                    if cw['w']:  # 过滤空字符
                        words.append(cw['w'])
        # 合并当前时间段的文字
        text_parts.append(''.join(words))

    # 合并所有时间段文字
    return ''.join(text_parts)

def speech_to_text(audio_path: str, app_id: str, api_key: str, api_secret: str) -> str:
    """
    调用讯飞语音识别API将语音转换为文字
    """
    try:
        from ..utils.speech_to_text_fast import speech_to_text as st
        
        # 转换音频格式
        new_name = convert_mp3_16k(audio_path)
        new_url = os.path.join(os.path.dirname(audio_path), new_name)
        
        # 调用语音识别
        result = st(new_url, app_id, api_key, api_secret)
        text_result = extract_words_from_lattice2(result)
        
        return text_result
    except Exception as e:
        logger.error(f"语音识别失败: {str(e)}")
        raise

def text_to_speech(text: str, app_id: str, api_secret: str, api_key: str, file_path: str) -> str:
    """
    调用讯飞语音合成API将文字转换为语音
    """
    try:

        # 调用语音合成
        file_name =tts(text, app_id, api_secret, api_key, file_path)
        
        return file_name
    except Exception as e:
        logger.error(f"语音合成失败: {str(e)}")
        raise 