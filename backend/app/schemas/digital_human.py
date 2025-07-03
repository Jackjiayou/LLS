from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class DigitalHumanCreateRequest(BaseModel):
    video_id: Optional[str] = None
    audio_id: Optional[str] = None

class DigitalHumanFileBase(BaseModel):
    """数字人文件基础模型"""
    file_type: str
    original_filename: str
    file_path: str
    file_size: int

class DigitalHumanFileCreate(DigitalHumanFileBase):
    """创建数字人文件模型"""
    pass

class DigitalHumanFileResponse(DigitalHumanFileBase):
    """数字人文件响应模型"""
    id: str
    user_id: str
    upload_time: datetime
    file_url: str

    class Config:
        from_attributes = True

class DigitalHumanBase(BaseModel):
    """数字人基础模型"""
    name: str
    image_file_id: Optional[str] = None
    video_file_id: Optional[str] = None
    audio_file_id: Optional[str] = None
    text_content: Optional[str] = None

class DigitalHumanCreate(DigitalHumanBase):
    """创建数字人模型"""
    pass

class DigitalHumanResponse(DigitalHumanBase):
    """数字人响应模型"""
    id: str
    user_id: str
    status: str
    create_time: datetime
    update_time: datetime
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None

    class Config:
        from_attributes = True

class DigitalHumanListResponse(BaseModel):
    """数字人列表响应模型"""
    success: bool
    data: List[DigitalHumanResponse]

class DigitalHumanDetailResponse(BaseModel):
    """数字人详情响应模型"""
    success: bool
    data: DigitalHumanResponse

class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    success: bool
    file_id: str
    file_url: str
    message: str

class DigitalHumanCreateResponse(BaseModel):
    """数字人创建响应模型"""
    success: bool
    digital_human_id: str
    message: str 