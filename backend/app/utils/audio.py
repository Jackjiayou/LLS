import os
from pydub import AudioSegment
from pydub.utils import which
import librosa
from ..core.config import settings

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

def convert_mp3_16k(audio_path: str) -> str:
    """
    将音频文件转换为16kHz采样率
    """
    AudioSegment.converter = which("ffmpeg")
    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    
    base, _ = os.path.splitext(audio_path)
    output_path = base + "_16k.mp3"
    
    audio.export(output_path, format="mp3")
    return os.path.basename(output_path)

def get_audio_duration(audio_path: str) -> float:
    """
    获取音频文件时长
    """
    y, sr = librosa.load(audio_path, sr=None)
    return round(librosa.get_duration(y=y, sr=sr))

def ensure_upload_dirs():
    """
    确保上传目录存在
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "tts"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "voice"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "download"), exist_ok=True) 