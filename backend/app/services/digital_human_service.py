import os
import uuid
import random
import librosa
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import UploadFile
from app.core.config import settings
from app.core.logger import logger

from fastapi import FastAPI, HTTPException
import  requests
import  time

class DigitalHumanService:
    def __init__(self):
        self.base_url = settings.BASE_URL + "/uploads/tts/"


def process_video(user_id,video_path, audio_path, api_url="http://117.50.194.151/:8000"):
    """
    处理视频和音频文件

    参数:
        video_path: 视频文件路径（MP4格式）
        audio_path: 音频文件路径（WAV格式）
        api_url: API服务器地址
    """
    # 1. 上传文件并获取任务ID
    files = {
        'video_file': ('input.mp4', open(video_path, 'rb'), 'video/mp4'),
        'audio_file': ('input.wav', open(audio_path, 'rb'), 'audio/wav')
    }

    print("开始上传文件...")
    response = requests.post(f"{api_url}/process/", files=files)
    if response.status_code != 200:
        print(f"上传失败: {response.text}")
        return

    task_id = response.json()['task_id']
    print(f"文件上传成功，任务ID: {task_id}")

    # 2. 循环检查处理状态
    while True:
        status_response = requests.get(f"{api_url}/status/{task_id}")
        print('get code status:'+str(status_response.status_code))
        if status_response.status_code == 502:
            print('502')
            continue
        status = status_response.json()
        print(f"当前状态: {status['status']}")

        if status['status'] == 'completed':
            # 3. 下载处理完成的视频
            print("处理完成，开始下载结果...")
            result_response = requests.get(f"{api_url}/result/{task_id}")

            if result_response.status_code == 200:
                user_dir = f"{ settings.UPLOAD_DIR}/digital_human/generate/{user_id}"
                os.makedirs(user_dir, exist_ok=True)
                output_filename = f"output_{task_id}_input.mp4"
                url_path = f"{settings.BASE_URL}/uploads/digital_human/generate/{user_id}/{output_filename}"
                output_path =f"{ user_dir}/{output_filename}"

                with open(output_path, 'wb') as f:
                    f.write(result_response.content)
                print(f"下载完成，保存到: {output_path}")
                return output_path,url_path
            else:
                print(f"下载失败: {result_response.text}")
                raise HTTPException(status_code=500, detail=f"获取机器人消息失败: {str(result_response.text)}")
            break

        elif status['status'] == 'failed':
            print(f"处理失败: {status.get('error', '未知错误')}")
            raise HTTPException(status_code=500, detail=f"获取机器人消息失败")
            break

        time.sleep(5)  # 每5秒检查一次状态


#
#
# # 新增依赖注入工厂
# def get_gh_service():
#     return DigitalHumanService()
