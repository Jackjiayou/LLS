from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form,Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.auth import get_current_user
from app.core.logger import logger, log_request, log_response, log_error
from app.models.digital_human import DigitalHuman, DigitalHumanFile
from app.schemas.digital_human import DigitalHumanCreateRequest

from  app.services.digital_human_service import  process_video,process_video_new

from app.core.config import settings
import os
import uuid
from datetime import datetime
from typing import Optional
import shutil
import traceback

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
            "file_url": f"{settings.BASE_URL}/uploads/digital_human/{relative_path}",
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
            "file_url": f"{settings.BASE_URL}/uploads/digital_human/{relative_path}",
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
            "file_url": f"{settings.BASE_URL}/uploads/digital_human/{relative_path}",
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
    db: Session = Depends(get_db)
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
            #audio_path =  os.path.join(settings.UPLOAD_DIR,audio_file.file_path)
            audio_path = f"{settings.uploads_url}{audio_file.file_path}"
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
            task_id = process_video_new(user_id, vidoe_path, audio_path)

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