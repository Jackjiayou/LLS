from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.core.auth import get_current_user

def require_admin(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """验证用户是否为管理员"""
    try:
        user_id = current_user.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"权限验证失败: {str(e)}") 