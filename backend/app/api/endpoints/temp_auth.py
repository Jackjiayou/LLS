from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import LoginRequest
from app.core.config import settings
from app.core.logger import logger
import requests
from datetime import datetime, timedelta
import jwt

router = APIRouter()

def create_temp_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, expire

@router.post("/temp-login")
async def temp_login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """临时登录接口，用于获取用户openid（绕过白名单验证）"""
    try:
        # 微信登录凭证校验
        url = f"https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": settings.APPID,
            "secret": settings.APPKEY,
            "js_code": login_data.code,
            "grant_type": "authorization_code"
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if "errcode" in result and result["errcode"] != 0:
            raise HTTPException(
                status_code=400,
                detail=f"微信登录失败：{result.get('errmsg', '未知错误')}"
            )
        
        if "openid" not in result:
            raise HTTPException(
                status_code=400,
                detail="微信登录返回数据不完整"
            )
        
        openid = result["openid"]
        session_key = result["session_key"]
        
        # 查找或创建用户
        user = db.query(User).filter(User.openid == openid).first()
        if not user:
            user = User(
                openid=openid,
                session_key=session_key,
                nickname=login_data.nickname,
                avatar_url=login_data.avatar_url
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            if login_data.nickname:
                user.nickname = login_data.nickname
            if login_data.avatar_url:
                user.avatar_url = login_data.avatar_url
            db.commit()
        
        # 创建临时访问令牌（有效期较短）
        access_token_expires = timedelta(minutes=30)  # 30分钟有效期
        access_token, expires_at = create_temp_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        logger.info(f"临时登录成功 - ID: {user.id}, openid: {openid}, nickname: {user.nickname}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": expires_at,
            "user_id": str(user.id),
            "openid": openid,  # 直接返回openid
            "nickname": user.nickname,  # 返回用户昵称
            "message": "临时登录成功，请复制openid后添加到白名单"
        }
        
    except Exception as e:
        logger.error(f"临时登录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"临时登录失败: {str(e)}") 