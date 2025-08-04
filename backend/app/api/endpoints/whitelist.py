from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.user import Whitelist, User, AuthorizationRequest
from app.core.auth import get_current_user
from app.core.admin_auth import require_admin
from app.core.auth_codes import is_valid_auth_code
from app.schemas.whitelist import WhitelistCreate, WhitelistResponse, WhitelistList, AuthorizationRequestCreate, AuthorizationRequestResponse, AuthorizationRequestList, AuthorizationRequestProcess

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

# 申请授权相关接口
@router.post("/auth-request/create", response_model=AuthorizationRequestResponse)
async def create_auth_request(
    request_data: AuthorizationRequestCreate,
    db: Session = Depends(get_db)
):
    """创建申请授权请求"""
    try:
        # 检查是否已有待处理的申请
        existing_pending = db.query(AuthorizationRequest).filter(
            AuthorizationRequest.openid == request_data.openid,
            AuthorizationRequest.status == "pending"
        ).first()
        
        if existing_pending:
            raise HTTPException(status_code=400, detail="您已有待处理的申请")
        
        # 检查是否已在白名单中
        existing_whitelist = db.query(Whitelist).filter(
            Whitelist.openid == request_data.openid,
            Whitelist.is_active == True
        ).first()
        
        if existing_whitelist:
            raise HTTPException(status_code=400, detail="您已在白名单中")
        
        # 授权码后门检查
        is_auto_approved = is_valid_auth_code(request_data.reason)
        
        # 创建申请
        auth_request = AuthorizationRequest(
            openid=request_data.openid,
            unionid=request_data.unionid,
            nickname=request_data.nickname,
            avatar_url=request_data.avatar_url,
            reason=request_data.reason
        )
        
        # 如果是授权码，直接设置为已批准状态
        if is_auto_approved:
            auth_request.status = "approved"
            auth_request.processed_at = datetime.now()
            auth_request.processed_by = "system"
            auth_request.processed_reason = "授权码自动批准"
            
            # 同时添加到白名单
            whitelist_item = Whitelist(
                openid=request_data.openid,
                unionid=request_data.unionid,
                nickname=request_data.nickname,
                added_by="system"
            )
            db.add(whitelist_item)
        
        db.add(auth_request)
        db.commit()
        db.refresh(auth_request)
        
        return AuthorizationRequestResponse(
            id=auth_request.id,
            openid=auth_request.openid,
            unionid=auth_request.unionid,
            nickname=auth_request.nickname,
            avatar_url=auth_request.avatar_url,
            reason=auth_request.reason,
            status=auth_request.status,
            requested_at=auth_request.requested_at,
            processed_at=auth_request.processed_at,
            processed_by=auth_request.processed_by,
            processed_reason=auth_request.processed_reason
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建申请失败: {str(e)}")

@router.get("/auth-request/list", response_model=AuthorizationRequestList)
async def get_auth_requests(
    status: Optional[str] = Query(None, description="筛选状态: pending, approved, rejected"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """获取申请授权列表（管理员）"""
    try:
        query = db.query(AuthorizationRequest)
        
        if status:
            query = query.filter(AuthorizationRequest.status == status)
        
        auth_requests = query.order_by(AuthorizationRequest.requested_at.desc()).all()
        
        return AuthorizationRequestList(
            items=[
                AuthorizationRequestResponse(
                    id=item.id,
                    openid=item.openid,
                    unionid=item.unionid,
                    nickname=item.nickname,
                    avatar_url=item.avatar_url,
                    reason=item.reason,
                    status=item.status,
                    requested_at=item.requested_at,
                    processed_at=item.processed_at,
                    processed_by=item.processed_by,
                    processed_reason=item.processed_reason
                ) for item in auth_requests
            ],
            total=len(auth_requests)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取申请列表失败: {str(e)}")

@router.get("/auth-request/my", response_model=AuthorizationRequestResponse)
async def get_my_auth_request(
    openid: str,
    db: Session = Depends(get_db)
):
    """获取我的申请状态"""
    try:
        auth_request = db.query(AuthorizationRequest).filter(
            AuthorizationRequest.openid == openid
        ).order_by(AuthorizationRequest.requested_at.desc()).first()
        
        if not auth_request:
            raise HTTPException(status_code=404, detail="未找到申请记录")
        
        return AuthorizationRequestResponse(
            id=auth_request.id,
            openid=auth_request.openid,
            unionid=auth_request.unionid,
            nickname=auth_request.nickname,
            avatar_url=auth_request.avatar_url,
            reason=auth_request.reason,
            status=auth_request.status,
            requested_at=auth_request.requested_at,
            processed_at=auth_request.processed_at,
            processed_by=auth_request.processed_by,
            processed_reason=auth_request.processed_reason
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取申请状态失败: {str(e)}")

@router.post("/auth-request/{request_id}/process")
async def process_auth_request(
    request_id: int,
    process_data: AuthorizationRequestProcess,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """处理申请授权请求（管理员）"""
    try:
        auth_request = db.query(AuthorizationRequest).filter(
            AuthorizationRequest.id == request_id
        ).first()
        
        if not auth_request:
            raise HTTPException(status_code=404, detail="申请不存在")
        
        if auth_request.status != "pending":
            raise HTTPException(status_code=400, detail="申请已被处理")
        
        # 更新申请状态
        auth_request.status = process_data.status
        auth_request.processed_at = datetime.now()
        auth_request.processed_by = str(admin_user.id)
        auth_request.processed_reason = process_data.reason
        
        # 如果批准，自动添加到白名单
        if process_data.status == "approved":
            whitelist_item = Whitelist(
                openid=auth_request.openid,
                unionid=auth_request.unionid,
                nickname=auth_request.nickname,
                added_by=str(admin_user.id)
            )
            db.add(whitelist_item)
        
        db.commit()
        
        return {"message": f"申请已{process_data.status == 'approved' and '批准' or '拒绝'}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"处理申请失败: {str(e)}")

@router.get("/auth-codes")
async def get_auth_codes(
    admin_user: User = Depends(require_admin)
):
    """获取授权码列表（仅管理员）"""
    from app.core.auth_codes import get_auth_codes
    return {"auth_codes": get_auth_codes()} 