from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.user import User
from app.core.admin_auth import require_admin
from app.schemas.admin import AdminUserResponse, AdminUserList

router = APIRouter()

@router.post("/admin/set-admin/{user_id}")
async def set_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """设置用户为管理员"""
    try:
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        target_user.is_admin = True
        db.commit()
        
        return {"message": f"用户 {target_user.nickname} 已设置为管理员"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"设置管理员失败: {str(e)}")

@router.post("/admin/remove-admin/{user_id}")
async def remove_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """移除用户的管理员权限"""
    try:
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        if target_user.id == admin_user.id:
            raise HTTPException(status_code=400, detail="不能移除自己的管理员权限")
        
        target_user.is_admin = False
        db.commit()
        
        return {"message": f"用户 {target_user.nickname} 的管理员权限已移除"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"移除管理员权限失败: {str(e)}")

@router.get("/admin/list", response_model=AdminUserList)
async def list_admin_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """获取管理员列表"""
    try:
        admin_users = db.query(User).filter(User.is_admin == True).all()
        
        return AdminUserList(
            items=[
                AdminUserResponse(
                    id=user.id,
                    openid=user.openid,
                    nickname=user.nickname,
                    is_admin=user.is_admin,
                    created_at=user.created_at
                ) for user in admin_users
            ],
            total=len(admin_users)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取管理员列表失败: {str(e)}") 