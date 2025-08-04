"""
授权码配置文件
"""

# 有效的授权码列表
VALID_AUTH_CODES = [
    "LLS2024",      # 主要授权码
    "AUTH2024",     # 备用授权码1
    "INVITE2024",   # 备用授权码2
    "VIP2024",      # VIP授权码
    "TEST2025"      # 测试授权码
]

def is_valid_auth_code(code: str) -> bool:
    """
    检查是否为有效的授权码
    
    Args:
        code: 要检查的授权码
        
    Returns:
        bool: 是否为有效授权码
    """
    if not code:
        return False
    
    return code.strip() in VALID_AUTH_CODES

def get_auth_codes() -> list:
    """
    获取所有有效的授权码列表
    
    Returns:
        list: 授权码列表
    """
    return VALID_AUTH_CODES.copy() 