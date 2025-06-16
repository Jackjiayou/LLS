from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, Token, UserBase, LoginRequest
from app.core.config import settings
from app.core.logger import logger, log_request, log_response, log_error
from app.core.auth import get_current_user
import jwt
from datetime import datetime, timedelta
import requests
from typing import Optional

__all__ = ['create_access_token', 'router']

router = APIRouter()

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, expire

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    try:
        # 记录登录请求
        log_request({
            "endpoint": "/login",
            "data": {
                "code": login_data.code,
                "nickname": login_data.nickname,
                "avatar_url": login_data.avatar_url
            }
        })

        # 微信登录凭证校验
        url = f"https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": settings.APPID,
            "secret": "d2ac10bec34434ee636c81db6d0d0167",
            "js_code": login_data.code,
            "grant_type": "authorization_code"
        }
        
        logger.info(f"正在请求微信登录接口，参数：{params}")
        response = requests.get(url, params=params)
        result = response.json()
        logger.info(f"微信登录接口返回：{result}")
        
        if "errcode" in result and result["errcode"] != 0:
            error_msg = f"微信登录失败：{result.get('errmsg', '未知错误')}"
            log_error({"error": error_msg, "wechat_response": result})
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        if "openid" not in result or "session_key" not in result:
            error_msg = "微信登录返回数据不完整"
            log_error({"error": error_msg, "wechat_response": result})
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        openid = result["openid"]
        session_key = result["session_key"]
        
        # 查找或创建用户
        user = db.query(User).filter(User.openid == openid).first()
        if not user:
            # 创建新用户时设置用户信息
            user = User(
                openid=openid,
                session_key=session_key,
                nickname=login_data.nickname,
                avatar_url=login_data.avatar_url
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"创建新用户：{user.id}")
        else:
            # 更新现有用户的信息
            if login_data.nickname:
                user.nickname = login_data.nickname
            if login_data.avatar_url:
                user.avatar_url = login_data.avatar_url
            db.commit()
            logger.info(f"更新已存在用户：{user.id}")
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token, expires_at = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": expires_at,
            "user_id": str(user.id)
        }
        
        # 记录成功响应
        log_response({
            "endpoint": "/login",
            "status": "success",
            "user_id": user.id,
            "expires_at": expires_at
        })
        
        return response_data
    except requests.RequestException as e:
        error_msg = f"请求微信接口失败：{str(e)}"
        log_error({"error": error_msg, "exception": str(e)})
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )
    except Exception as e:
        error_msg = f"登录失败：{str(e)}"
        log_error({"error": error_msg, "exception": str(e)})
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.post("/refresh-token", response_model=Token)
async def refresh_token(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token, expires_at = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expires_at
    }

@router.get("/user-info")
async def get_user_info(token: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == token["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "nickname": user.nickname,
        "avatar_url": user.avatar_url
    }

@router.post("/update-user-info")
async def update_user_info(
    user_info: UserBase,
    token: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == token["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.nickname = user_info.nickname
    user.avatar_url = user_info.avatar_url
    db.commit()
    
    return {"message": "User info updated successfully"} 