from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form,Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.auth import get_current_user
from app.core.logger import logger, log_request, log_response, log_error
from app.models.digital_human import DigitalHuman, DigitalHumanFile, DigitalHumanClone, VoiceClone, DigitalHumanSynthesis, VoiceSynthesis
from app.schemas.digital_human import DigitalHumanCreateRequest

from  app.services.digital_human_service import get_gh_service

from app.core.config import settings
import os
import uuid
from datetime import datetime
from typing import Optional
import shutil
import traceback
from  app.utils.audio import  convert_mp3_16k
import requests
from datetime import datetime, timedelta

router = APIRouter()

# 文件上传目录
UPLOAD_DIR = os.path.join(settings.UPLOAD_DIR, "digital_human")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".wmv", ".flv"}
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return os.path.splitext(filename)[1].lower()

def is_allowed_file(filename: str, allowed_extensions: set) -> bool:
    """检查文件类型是否允许"""
    return get_file_extension(filename) in allowed_extensions

def save_uploaded_file(file: UploadFile, file_type: str, user_id: str) -> tuple[str, str]:
    """保存上传的文件到以用户ID为子目录的路径"""
    file_extension = get_file_extension(file.filename)
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # 创建类型+用户ID子目录
    type_dir = os.path.join(UPLOAD_DIR, file_type, user_id)
    os.makedirs(type_dir, exist_ok=True)

    file_path = os.path.join(type_dir, unique_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 返回相对路径和完整路径
    relative_path = f"digital_human/{file_type}/{user_id}/{unique_filename}"
    return relative_path, file_path

@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传图片文件"""
    try:
        log_request({
            "endpoint": "/upload-image",
            "user_id": current_user["sub"],
            "filename": file.filename
        })
        
        # 检查文件类型
        if not is_allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail="不支持的文件类型，请上传图片文件"
            )
        
        # 检查文件大小 (限制为10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="文件大小不能超过10MB"
            )
        
        # 保存文件
        relative_path, file_path = save_uploaded_file(file, "images", current_user["sub"])
        
        # 保存到数据库
        db_file = DigitalHumanFile(
            user_id=current_user["sub"],
            file_type="image",
            original_filename=file.filename,
            file_path=relative_path,
            file_size=file.size or 0,
            upload_time=datetime.utcnow()
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        response_data = {
            "success": True,
            "file_id": str(db_file.id),
            "file_url": f"{settings.uploads_url}/{relative_path}",
            "message": "图片上传成功"
        }
        
        log_response({
            "endpoint": "/upload-image",
            "status": "success",
            "file_id": str(db_file.id)
        })
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        log_error({
            "endpoint": "/upload-image",
            "error": str(e),
            "user_id": current_user["sub"]
        })
        raise HTTPException(
            status_code=500,
            detail="图片上传失败"
        )

@router.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传视频文件"""
    try:
        log_request({
            "endpoint": "/upload-video",
            "user_id": current_user["sub"],
            "filename": file.filename
        })
        
        # 检查文件类型
        if not is_allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail="不支持的文件类型，请上传视频文件"
            )
        
        # 检查文件大小 (限制为100MB)
        if file.size and file.size > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="文件大小不能超过100MB"
            )
        
        # 保存文件
        relative_path, file_path = save_uploaded_file(file, "videos", current_user["sub"])
        
        # 保存到数据库
        db_file = DigitalHumanFile(
            user_id=current_user["sub"],
            file_type="video",
            original_filename=file.filename,
            file_path=relative_path,
            file_size=file.size or 0,
            upload_time=datetime.utcnow()
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        response_data = {
            "success": True,
            "file_id": str(db_file.id),
            "file_url": f"{settings.uploads_url}/{relative_path}",
            "message": "视频上传成功"
        }
        
        log_response({
            "endpoint": "/upload-video",
            "status": "success",
            "file_id": str(db_file.id)
        })
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        log_error({
            "endpoint": "/upload-video",
            "error": str(e),
            "user_id": current_user["sub"]
        })
        raise HTTPException(
            status_code=500,
            detail="视频上传失败"
        )

@router.post("/upload-audio")
async def upload_audio(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传音频文件"""
    try:
        log_request({
            "endpoint": "/upload-audio",
            "user_id": current_user["sub"],
            "filename": file.filename
        })
        
        # 检查文件类型
        if not is_allowed_file(file.filename, ALLOWED_AUDIO_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail="不支持的文件类型，请上传音频文件"
            )
        
        # 检查文件大小 (限制为50MB)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="文件大小不能超过50MB"
            )
        
        # 保存文件
        relative_path, file_path = save_uploaded_file(file, "audios", current_user["sub"])
        
        # 保存到数据库
        db_file = DigitalHumanFile(
            user_id=current_user["sub"],
            file_type="audio",
            original_filename=file.filename,
            file_path=relative_path,
            file_size=file.size or 0,
            upload_time=datetime.utcnow()
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        response_data = {
            "success": True,
            "file_id": str(db_file.id),
            "file_url": f"{settings.uploads_url}/{relative_path}",
            "message": "音频上传成功"
        }
        
        log_response({
            "endpoint": "/upload-audio",
            "status": "success",
            "file_id": str(db_file.id)
        })
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        log_error({
            "endpoint": "/upload-audio",
            "error": str(e),
            "user_id": current_user["sub"]
        })
        raise HTTPException(
            status_code=500,
            detail="音频上传失败"
        )

@router.post("/create")
async def create_digital_human(
    req: DigitalHumanCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    dh_service = Depends(get_gh_service)
):
    """创建数字人"""
    try:
        user_id =  current_user["sub"]
        vidoe_path = ''
        audio_path = ''
        video_id = req.video_id
        audio_id = req.audio_id
        log_request({
            "endpoint": "/create",
            "user_id": current_user["sub"],
            "data": {
                "video_id": video_id,
                "audio_id": audio_id
            }
        })
        
        # 验证至少有一个素材
        if not any([video_id, audio_id]):
            raise HTTPException(
                status_code=400,
                detail="请至少上传一个素材"
            )
        
        # 验证文件是否存在且属于当前用户
        files = []
        
        if video_id:
            video_file = db.query(DigitalHumanFile).filter(
                DigitalHumanFile.id == video_id,
                DigitalHumanFile.user_id == current_user["sub"],
                DigitalHumanFile.file_type == "video"
            ).first()
            if not video_file:
                raise HTTPException(status_code=404, detail="视频文件不存在")
            files.append(video_file)
            #vidoe_path = os.path.join(settings.UPLOAD_DIR,video_file.file_path)
            vidoe_path = f"{settings.uploads_url}{video_file.file_path}"

        
        if audio_id:
            audio_file = db.query(DigitalHumanFile).filter(
                DigitalHumanFile.id == audio_id,
                DigitalHumanFile.user_id == current_user["sub"],
                DigitalHumanFile.file_type == "audio"
            ).first()
            if not audio_file:
                raise HTTPException(status_code=404, detail="音频文件不存在")
            files.append(audio_file)
            #local_audio_path =  os.path.join(settings.UPLOAD_DIR,audio_file.file_path)
            #new_name = convert_mp3_16k(local_audio_path)
            audio_path = f"{settings.uploads_url}{audio_file.file_path}"
            #audio_path = f"{settings.uploads_url}{new_name}"
        # 创建数字人记录m
        digital_human = DigitalHuman(
            user_id=current_user["sub"],
            name=f"数字人_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            video_file_id=video_id,
            audio_file_id=audio_id,
            status="processing",  # processing, completed, failed
            create_time=datetime.utcnow()
        )
        db.add(digital_human)
        db.commit()
        db.refresh(digital_human)


        # 调用第三方接口获取任务ID
        try:
            task_id = 624129
            task_id = dh_service.process_video_new(user_id, vidoe_path, audio_path)

            # 更新数字人记录，保存任务ID
            digital_human.task_id = task_id
            db.commit()
            
            response_data = {
                "success": True,
                "digital_human_id": str(digital_human.id),
                "task_id": task_id,
                "message": "数字人创建成功，正在处理中"
            }
            
        except Exception as e:
            # 如果调用第三方接口失败，更新状态为失败
            digital_human.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail=f"调用第三方接口失败: {str(e)}")
        
        log_response({
            "endpoint": "/create",
            "status": "success",
            "digital_human_id": str(digital_human.id),
            "task_id": task_id
        })
        
        return response_data

    except HTTPException:
        traceback.print_exc()
        raise
    except Exception as e:
        traceback.print_exc()
        log_error({
            "endpoint": "/create",
            "error": traceback.format_exc(),
            "user_id": current_user["sub"]
        })
        raise HTTPException(status_code=500, detail=f"调用第三方接口失败: {str(e)}")

@router.post("/create_digital_human_callback")
async def create_digital_human_callback(
request: Request
):
    """创建数字人回调接口 - 第三方接口处理完成后调用"""
    try:
        data = await request.json()
        log_request({
            "create_digital_human_callback data": data,
        })

        print("✅ 原始回调数据：", data)
        
        # 解析回调数据
        if data.get('code') == 200 and data.get('data'):
            callback_data = data['data']
            video_task_id = callback_data.get('video_task_id')
            video_url = callback_data.get('videoUrl')
            cover_url = callback_data.get('coverUrl')
            duration = callback_data.get('duration')
            bill_id = callback_data.get('bill_id')
            
            print(f"✅ 解析回调数据：task_id={video_task_id}, video_url={video_url}")
            
            # 根据task_id查找对应的数字人记录
            db = next(get_db())
            digital_human = db.query(DigitalHuman).filter(
                DigitalHuman.task_id == str(video_task_id)
            ).first()
            
            if digital_human:
                # 更新数字人状态和视频路径
                digital_human.status = "completed"
                digital_human.generate_video_path = video_url
                digital_human.update_time = datetime.utcnow()
                db.commit()
                
                print(f"✅ 数字人 {digital_human.id} 处理完成，视频地址: {video_url}")
                
                # 记录成功日志
                log_response({
                    "endpoint": "/create_digital_human_callback",
                    "status": "success",
                    "digital_human_id": str(digital_human.id),
                    "video_url": video_url
                })
                
            else:
                print(f"❌ 未找到任务ID为 {video_task_id} 的数字人记录")
                log_error({
                    "endpoint": "/create_digital_human_callback",
                    "error": f"未找到任务ID为 {video_task_id} 的数字人记录"
                })
        else:
            print(f"❌ 回调数据格式错误: {data}")
            log_error({
                "endpoint": "/create_digital_human_callback",
                "error": f"回调数据格式错误: {data}"
            })
        
        return {"success": True, "message": "回调处理完成"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_error({
            "endpoint": "/create_digital_human_callback",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="回调处理失败")

@router.post("/clone-human")
async def clone_human(
    video_url: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    try:
        """发起克隆数字人"""
        clone = DigitalHumanClone(
            user_id=current_user["sub"],
            name=name,
            video_url=video_url,
            status="processing",
            create_time=datetime.utcnow(),
            update_time=datetime.utcnow()
        )
        db.add(clone)
        db.commit()
        db.refresh(clone)
        #video_url = 'https://ai.dl-dd.com/uploads/download/hi1.mp4'  #todo
        resp = requests.post(
            "https://api.yidevs.com/app/human/human/Scene/created",
            # "callback_url": f"{settings.BASE_URL}/api/digital-human/clone-human-callback",
            json={
                "callback_url": "https://ai.dl-dd.com/api/digital-human/clone-human-callback",
                "video_url": video_url,
                "video_name": "test"
            },
            headers={
                "Authorization": f"{settings.xjyTOKEN}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        data = resp.json()
        if data.get("code") == 200 and data.get("data", {}).get("scene_task_id"):
            scene_task_id = str(data["data"]["scene_task_id"])
            clone.scene_task_id = scene_task_id
            db.commit()
            return {"success": True, "scene_task_id": scene_task_id}
        else:
            clone.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail="第三方API返回异常")
    except Exception as e:
        clone.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"第三方API调用失败: {e}")

@router.post("/clone-human-callback")
async def clone_human_callback(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    if data.get('code') == 200 and data.get('data'):
        callback_data = data['data']
        scene_task_id = str(callback_data.get('scene_task_id') or callback_data.get('sceneId'))
        video_url = callback_data.get('videoUrl')
        cover_url = callback_data.get('coverUrl')
        clone = db.query(DigitalHumanClone).filter_by(scene_task_id=scene_task_id).first()
        if clone:
            clone.status = "completed"
            clone.video_url = video_url
            clone.cover_url = cover_url
            clone.update_time = datetime.utcnow()
            db.commit()
    return {"success": True}


@router.get("/synthesize-list")
async def get_synthesize_list(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取用户的合成数字人列表（只显示24小时内的）"""
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=24)
    syntheses = db.query(DigitalHumanSynthesis).filter(
        DigitalHumanSynthesis.user_id == current_user["sub"],
        DigitalHumanSynthesis.create_time > cutoff
    ).order_by(DigitalHumanSynthesis.create_time.desc()).all()

    result = []
    for synthesis in syntheses:
        result.append({
            "video_task_id": synthesis.video_task_id,
            "scene_task_id": synthesis.scene_task_id,
            "status": synthesis.status,
            "video_url": synthesis.video_url,
            "cover_url": synthesis.cover_url,
            "duration": synthesis.duration,
            "create_time": synthesis.create_time.isoformat(),
            "update_time": synthesis.update_time.isoformat() if synthesis.update_time else None
        })

    return {
        "success": True,
        "data": result
    }

@router.get("/clone-human-status/{scene_task_id}")
async def clone_human_status(scene_task_id: str, db: Session = Depends(get_db)):
    clone = db.query(DigitalHumanClone).filter_by(scene_task_id=scene_task_id).first()
    if not clone:
        raise HTTPException(status_code=404, detail="分身克隆任务不存在")
    return {
        "success": True,
        "data": {
            "scene_task_id": clone.scene_task_id,
            "status": clone.status,
            "video_url": clone.video_url,
            "cover_url": clone.cover_url,
            "name": clone.name,
            "update_time": clone.update_time
        }
    }

@router.post("/clone-voice")
async def clone_voice(
    audio_url: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    #todo
    # 记录登录请求
    log_request({
        "endpoint": "/clone_voice",
        "data": {
            "audio_url": audio_url
        }
    })
    audio_url = 'https://ai.dl-dd.com/uploads/download/1747033032.mp3'
    """发起克隆语音"""
    voice_clone = VoiceClone(
        user_id=current_user["sub"],
        name=name,
        audio_url=audio_url,
        status="processing",
        create_time=datetime.utcnow(),
        update_time=datetime.utcnow()
    )
    db.add(voice_clone)
    db.commit()
    db.refresh(voice_clone)
    
    try:
        logger.info(f"clone_voice   audio_url: {audio_url}")
        resp = requests.post(
            "https://api.yidevs.com/app/human/human/Voice/clone",
            json={
                "name": name,
                "audio_url": audio_url,
                "description": description
            },
            headers={
                "Authorization": f"{settings.YIDEVS_KEY}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        data = resp.json()
        if data.get("code") == 200 and data.get("data", {}).get("voice_id"):
            voice_id = data["data"]["voice_id"]
            task_id = data["data"].get("task_id")
            voice_clone.voice_id = voice_id
            voice_clone.task_id = str(task_id) if task_id else None
            # 克隆语音是同步完成的，直接设置状态为completed
            voice_clone.status = "completed"
            voice_clone.update_time = datetime.utcnow()
            db.commit()
            return {"success": True, "voice_id": voice_id, "task_id": task_id}
        else:
            voice_clone.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail="第三方API返回异常")
    except Exception as e:
        voice_clone.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"第三方API调用失败: {e}")

@router.get("/clone-voice-status/{voice_id}")
async def clone_voice_status(voice_id: str, db: Session = Depends(get_db)):
    """查询音色克隆状态"""
    voice_clone = db.query(VoiceClone).filter_by(voice_id=voice_id).first()
    if not voice_clone:
        raise HTTPException(status_code=404, detail="音色克隆任务不存在")
    return {
        "success": True,
        "data": {
            "voice_id": voice_clone.voice_id,
            "status": voice_clone.status,
            "name": voice_clone.name,
            "audio_url": voice_clone.audio_url,
            "update_time": voice_clone.update_time
        }
    }

@router.get("/voices")
async def get_voice_list(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的音色列表"""
    voice_clones = db.query(VoiceClone).filter(
        VoiceClone.user_id == current_user["sub"]
    ).order_by(VoiceClone.create_time.desc()).all()
    
    result = []
    for voice in voice_clones:
        result.append({
            "voice_id": voice.voice_id,
            "name": voice.name,
            "status": voice.status,
            "audio_url": voice.audio_url,
            "create_time": voice.create_time.isoformat()
        })
    
    return {
        "success": True,
        "data": result
    }

@router.get("/clones")
async def get_clone_list(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的分身列表"""
    clones = db.query(DigitalHumanClone).filter(
        DigitalHumanClone.user_id == current_user["sub"]
    ).order_by(DigitalHumanClone.create_time.desc()).all()
    
    result = []
    for clone in clones:
        result.append({
            "scene_task_id": clone.scene_task_id,
            "name": clone.name,
            "status": clone.status,
            "video_url": clone.video_url,
            "cover_url": clone.cover_url,
            "create_time": clone.create_time.isoformat()
        })
    
    return {
        "success": True,
        "data": result
    }


@router.get("/list")
async def get_digital_human_list(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的数字人列表"""
    try:
        digital_humans = db.query(DigitalHuman).filter(
            DigitalHuman.user_id == current_user["sub"]
        ).order_by(DigitalHuman.create_time.desc()).all()
        
        result = []
        for dh in digital_humans:
            result.append({
                "id": str(dh.id),
                "name": dh.name,
                "status": dh.status,
                "create_time": dh.create_time.isoformat(),
                "image_url": f"{settings.BASE_URL}/uploads/digital_human/{dh.image_file.file_path}" if dh.image_file else None
            })
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        log_error({
            "endpoint": "/list",
            "error": str(e),
            "user_id": current_user["sub"]
        })
        raise HTTPException(
            status_code=500,
            detail="获取数字人列表失败"
        )

@router.get("/{digital_human_id}")
async def get_digital_human_detail(
    digital_human_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取数字人详情"""
    try:
        digital_human = db.query(DigitalHuman).filter(
            DigitalHuman.id == digital_human_id,
            DigitalHuman.user_id == current_user["sub"]
        ).first()
        
        if not digital_human:
            raise HTTPException(status_code=404, detail="数字人不存在")
        
        return {
            "success": True,
            "data": {
                "id": str(digital_human.id),
                "name": digital_human.name,
                "status": digital_human.status,
                "create_time": digital_human.create_time.isoformat(),
                "image_url": f"{settings.BASE_URL}/uploads/digital_human/{digital_human.image_file.file_path}" if digital_human.image_file else None,
                "video_url": f"{settings.BASE_URL}/uploads/digital_human/{digital_human.video_file.file_path}" if digital_human.video_file else None,
                "audio_url": f"{settings.BASE_URL}/uploads/digital_human/{digital_human.audio_file.file_path}" if digital_human.audio_file else None,
                "text_content": digital_human.text_content
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error({
            "endpoint": f"/{digital_human_id}",
            "error": str(e),
            "user_id": current_user["sub"]
        })
        raise HTTPException(
            status_code=500,
            detail="获取数字人详情失败"
        ) 

@router.get("/status/{digital_human_id}")
async def get_digital_human_status(
    digital_human_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取数字人处理状态 - 用于前端轮询"""
    try:
        # 查询数字人记录
        #digital_human_id ='a4e8e602-f985-45d8-aba9-23c752351580'# "9f8d3096-1a8e-4c65-9f68-1f85c431d8a4"
        digital_human = db.query(DigitalHuman).filter(
            DigitalHuman.id == digital_human_id,
            DigitalHuman.user_id == current_user["sub"]
        ).first()
        
        if not digital_human:
            raise HTTPException(status_code=404, detail="数字人不存在")
        
        # 返回状态信息
        return {
            "success": True,
            "data": {
                "id": str(digital_human.id),
                "name": digital_human.name,
                "status": digital_human.status,  # processing, completed, failed
                "task_id": digital_human.task_id,
                "generate_video_path": digital_human.generate_video_path,  # 完成时才有值
                "create_time": digital_human.create_time.isoformat(),
                "update_time": digital_human.update_time.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error({
            "endpoint": f"/status/{digital_human_id}",
            "error": str(e),
            "user_id": current_user["sub"]
        })
        raise HTTPException(
            status_code=500,
            detail="获取数字人状态失败"
        ) 

@router.post("/voice-synthesis")
async def voice_synthesis(
    voice_id: str = Form(...),
    text: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """音频合成"""
    try:
        log_request({
            "endpoint": "/voice-synthesis",
            "user_id": current_user["sub"],
            "voice_id": voice_id,
            "text": text
        })
        
        # 检查音色是否存在且已完成
        voice = db.query(VoiceClone).filter_by(voice_id=voice_id).first()
        if not voice:
            raise HTTPException(status_code=404, detail="音色不存在")
        if voice.status != "completed":
            raise HTTPException(status_code=400, detail="音色尚未完成，无法合成音频")
        
        # 创建音频合成记录
        synthesis = VoiceSynthesis(
            user_id=current_user["sub"],
            voice_id=voice_id,
            text=text,
            status="processing"
        )
        db.add(synthesis)
        db.commit()
        db.refresh(synthesis)
        
        # 调用第三方API进行音频合成
        url = 'https://api.yidevs.com/app/human/human/Voice/created'
        headers = {
            'Authorization': settings.YIDEVS_KEY,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "text": text,
            "voice_id": voice_id
        }
        
        logger.info(f'Voice synthesis payload: {payload}')
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f'Voice synthesis response: {response.json()}')
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                # 音频合成是同步完成的，直接更新状态
                audio_url = result.get('data', {}).get('audio_url')
                synthesis.status = "completed"
                synthesis.audio_url = audio_url
                synthesis.update_time = datetime.utcnow()
                db.commit()
                
                return {
                    "success": True,
                    "data": {
                        "synthesis_id": str(synthesis.id),
                        "audio_url": audio_url,
                        "message": "音频合成完成"
                    }
                }
            else:
                synthesis.status = "failed"
                db.commit()
                raise HTTPException(status_code=500, detail=f"第三方API返回错误: {result.get('message', '未知错误')}")
        else:
            synthesis.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail=f"第三方API调用失败: {response.text}")
            
    except HTTPException:
        raise
    except Exception as e:
        log_error({
            "endpoint": "/voice-synthesis",
            "error": str(e),
            "user_id": current_user["sub"]
        })
        raise HTTPException(status_code=500, detail=f"音频合成失败: {str(e)}")

@router.get("/voice-synthesis-status/{synthesis_id}")
async def voice_synthesis_status(synthesis_id: str, db: Session = Depends(get_db)):
    """查询音频合成状态"""
    synthesis = db.query(VoiceSynthesis).filter_by(id=synthesis_id).first()
    if not synthesis:
        raise HTTPException(status_code=404, detail="音频合成任务不存在")
    
    return {
        "success": True,
        "data": {
            "synthesis_id": str(synthesis.id),
            "voice_id": synthesis.voice_id,
            "text": synthesis.text,
            "status": synthesis.status,
            "audio_url": synthesis.audio_url,
            "update_time": synthesis.update_time
        }
    }

@router.get("/voice-synthesis-list")
async def get_voice_synthesis_list(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的音频合成列表"""
    syntheses = db.query(VoiceSynthesis).filter(
        VoiceSynthesis.user_id == current_user["sub"]
    ).order_by(VoiceSynthesis.create_time.desc()).all()
    
    result = []
    for synthesis in syntheses:
        result.append({
            "synthesis_id": str(synthesis.id),
            "voice_id": synthesis.voice_id,
            "text": synthesis.text,
            "status": synthesis.status,
            "audio_url": synthesis.audio_url,
            "create_time": synthesis.create_time.isoformat()
        })
    
    return {
        "success": True,
        "data": result
    }

@router.post("/synthesize")
async def synthesize_digital_human(
    scene_task_id: str = Form(...),
    voice_id: str = Form(...),
    text: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发起数字人合成"""
    try:
        log_request({
            "endpoint": "/synthesize",
            "user_id": current_user["sub"],
            "scene_task_id": scene_task_id,
            "voice_id": voice_id,
            "text": text
        })
        
        # 检查分身是否存在且已完成
        clone = db.query(DigitalHumanClone).filter_by(scene_task_id=scene_task_id).first()
        if not clone:
            raise HTTPException(status_code=404, detail="分身不存在")
        if clone.status != "completed":
            raise HTTPException(status_code=400, detail="分身尚未完成，无法合成")
        
        # 检查音色是否存在且已完成
        voice = db.query(VoiceClone).filter_by(voice_id=voice_id).first()
        if not voice:
            raise HTTPException(status_code=404, detail="音色不存在")
        if voice.status != "completed":
            raise HTTPException(status_code=400, detail="音色尚未完成，无法合成")
        
        # 生成唯一的视频任务ID
        video_task_id = f"video_{uuid.uuid4().hex}"
        #video_task_id = video_task_id,
        # 创建合成记录
        synthesis = DigitalHumanSynthesis(
            user_id=current_user["sub"],
            scene_task_id=scene_task_id,
            status="processing"
        )
        db.add(synthesis)
        db.commit()
        db.refresh(synthesis)
        
        # 第一步：先合成音频
        audio_synthesis_url = 'https://api.yidevs.com/app/human/human/Voice/created'
        audio_headers = {
            'Authorization': settings.YIDEVS_KEY,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        audio_payload = {
            "text": text,
            "voice_id": voice_id
        }
        
        logger.info(f'Audio synthesis payload: {audio_payload}')
        audio_response = requests.post(audio_synthesis_url, json=audio_payload, headers=audio_headers)
        logger.info(f'Audio synthesis response: {audio_response.json()}')
        
        if audio_response.status_code != 200:
            synthesis.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail="音频合成失败")
        
        audio_result = audio_response.json()
        if audio_result.get('code') != 200:
            synthesis.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail=f"音频合成失败: {audio_result.get('message', '未知错误')}")
        
        # 获取合成的音频URL
        audio_url = audio_result.get('data', {}).get('audio_url')
        #audio_url='https://ai.dl-dd.com/uploads/download/1747033032.mp3'  #todo
        if not audio_url:
            synthesis.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail="音频合成失败：未获取到音频URL")
        
        # 第二步：调用数字人合成接口
        synthesis_url = 'https://api.yidevs.com/app/human/human/Index/created'
        synthesis_headers = {
            'Authorization': settings.YIDEVS_KEY,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        synthesis_payload = {
            "callback_url": f"{settings.BASE_URL}/api/digital-human/synthesize-callback",
            "audio_url": audio_url,
            "scene_task_id": scene_task_id
        }
        
        logger.info(f'Digital human synthesis payload: {synthesis_payload}')
        synthesis_response = requests.post(synthesis_url, json=synthesis_payload, headers=synthesis_headers)
        logger.info(f'Digital human synthesis response: {synthesis_response.json()}')
        
        if synthesis_response.status_code == 200:
            result = synthesis_response.json()
            if result.get('code') == 200:
                synthesis.video_task_id = result['data']['video_task_id']
                db.commit()
                return {
                    "success": True,
                    "data": {
                        "video_task_id": result['data']['video_task_id'],
                        "message": "合成任务已提交"
                    }
                }
            else:
                synthesis.status = "failed"
                db.commit()
                raise HTTPException(status_code=500, detail=f"第三方API返回错误: {result.get('message', '未知错误')}")
        else:
            synthesis.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail=f"第三方API调用失败: {synthesis_response.text}")
            
    except HTTPException:
        raise
    except Exception as e:
        log_error({
            "endpoint": "/synthesize",
            "error": str(e),
            "user_id": current_user["sub"]
        })
        raise HTTPException(status_code=500, detail=f"合成数字人失败: {str(e)}")

@router.post("/synthesize-callback")
async def synthesize_callback(request: Request, db: Session = Depends(get_db)):
    """合成数字人回调处理"""
    try:
        body = await request.json()
        logger.info(f'Synthesize callback received: {body}')

        code = body.get('code')
        msg = body.get('msg')
        data = body.get('data', {})

        video_task_id =  str(data.get('video_task_id'))
        video_url = data.get('videoUrl')
        cover_url = data.get('coverUrl')
        duration = data.get('duration')

        if not video_task_id:
            raise HTTPException(status_code=400, detail="缺少video_task_id参数")

        synthesis = db.query(DigitalHumanSynthesis).filter_by(video_task_id=video_task_id).first()
        if not synthesis:
            raise HTTPException(status_code=404, detail="合成任务不存在")

        # 设置状态
        if code == 200:
            synthesis.status = "completed"
        else:
            synthesis.status = "failed"

        synthesis.video_url = video_url
        synthesis.cover_url = cover_url
        synthesis.duration = duration
        synthesis.update_time = datetime.utcnow()

        db.commit()

        return {"success": True, "message": "回调处理成功"}

    except Exception as e:
        logger.error(f'Synthesize callback error: {str(e)}')
        raise HTTPException(status_code=500, detail=f"回调处理失败: {str(e)}")

@router.get("/synthesize-status/{video_task_id}")
async def synthesize_status(video_task_id: str, db: Session = Depends(get_db)):
    """查询合成数字人状态"""
    # 先通过video_task_id查找
    synthesis = db.query(DigitalHumanSynthesis).filter_by(video_task_id=video_task_id).first()

    
    if not synthesis:
        raise HTTPException(status_code=404, detail="合成任务不存在")
    
    return {
        "success": True,
        "data": {
            "video_task_id": synthesis.video_task_id,
            "scene_task_id": synthesis.scene_task_id,
            "status": synthesis.status,
            "video_url": synthesis.video_url,
            "cover_url": synthesis.cover_url,
            "duration": synthesis.duration,
            "update_time": synthesis.update_time
        }
    }

