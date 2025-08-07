#!/bin/bash

# 激活虚拟环境（可选，如果你不是用 systemd 控制的话）
# source /root/anaconda/home/anaconda/bin/activate test3

echo "🔄 Restarting FastAPI service..."
sudo systemctl daemon-reexec        # 重新初始化 systemd（保险）
sudo systemctl daemon-reload        # 重新加载 service 文件（如果改了）
sudo systemctl restart fastapi      # 重启服务
sleep 2                             # 等待服务重启

# 打印状态
echo "Service status:"
sudo systemctl status fastapi --no-pager

# 实时输出日志（按 Ctrl+C 退出）
echo "📄 Real-time logs:"
sudo journalctl -u fastapi -f
