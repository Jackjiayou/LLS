from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.user import Whitelist, User
from app.core.auth import get_current_user
from app.core.admin_auth import require_admin
from app.schemas.whitelist import WhitelistCreate, WhitelistResponse, WhitelistList

router = APIRouter()

@router.post("/whitelist/add", response_model=WhitelistResponse)
async def add_to_whitelist(
    openid: str,
    unionid: Optional[str] = None,
    nickname: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """添加用户到白名单"""
    try:
        # 检查是否已存在
        existing = db.query(Whitelist).filter(Whitelist.openid == openid).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户已在白名单中")
        
        # 添加到白名单
        whitelist_item = Whitelist(
            openid=openid,
            unionid=unionid,
            nickname=nickname,
            added_by=str(admin_user.id)
        )
        db.add(whitelist_item)
        db.commit()
        db.refresh(whitelist_item)
        
        return WhitelistResponse(
            id=whitelist_item.id,
            openid=whitelist_item.openid,
            unionid=whitelist_item.unionid,
            nickname=whitelist_item.nickname,
            added_at=whitelist_item.added_at,
            is_active=whitelist_item.is_active
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加白名单失败: {str(e)}")

@router.get("/whitelist/list", response_model=WhitelistList)
async def get_whitelist(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """获取白名单列表"""
    try:
        whitelist_items = db.query(Whitelist).filter(Whitelist.is_active == True).all()
        
        return WhitelistList(
            items=[
                WhitelistResponse(
                    id=item.id,
                    openid=item.openid,
                    unionid=item.unionid,
                    nickname=item.nickname,
                    added_at=item.added_at,
                    is_active=item.is_active
                ) for item in whitelist_items
            ],
            total=len(whitelist_items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取白名单失败: {str(e)}")

@router.delete("/whitelist/remove/{openid}")
async def remove_from_whitelist(
    openid: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """从白名单中移除用户"""
    try:
        whitelist_item = db.query(Whitelist).filter(Whitelist.openid == openid).first()
        if not whitelist_item:
            raise HTTPException(status_code=404, detail="用户不在白名单中")
        
        whitelist_item.is_active = False
        db.commit()
        
        return {"message": "用户已从白名单中移除"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"移除白名单失败: {str(e)}") 