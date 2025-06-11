import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 创建日志目录
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 生成日志文件名，包含日期
log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")

# 创建日志记录器
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建文件处理器
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)

# 创建格式化器
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# 添加处理器到记录器
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 创建一个函数来记录请求日志
def log_request(request_info: dict):
    logger.info(f"Request: {request_info}")

# 创建一个函数来记录响应日志
def log_response(response_info: dict):
    logger.info(f"Response: {response_info}")

# 创建一个函数来记录错误日志
def log_error(error_info: dict):
    logger.error(f"Error: {error_info}") 