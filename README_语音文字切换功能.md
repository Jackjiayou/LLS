# 语音和文字切换功能实现说明

## 功能概述
在原有的人机对话系统中，用户只能发送语音消息。现在新增了文字输入功能，用户可以自由切换语音和文字两种输入模式，模仿微信的发送信息体验。

## 主要修改

### 前端修改 (pages/assistant/assistant.vue)

#### 1. 新增数据属性
```javascript
inputMode: 'voice', // 输入模式：'voice' 或 'text'
inputText: '', // 文字输入框的值
```

#### 2. 修改输入区域UI
- 添加了输入模式切换按钮（🎤/⌨️）
- 新增文字输入模式：包含输入框和发送按钮
- 保留原有语音输入模式
- 优化了样式，模仿微信界面

#### 3. 新增方法
- `toggleInputMode()`: 切换输入模式
- `sendTextMessage()`: 发送文本消息，包括：
  - 添加用户消息到列表
  - 调用后端接口处理文本消息
  - 获取机器人回复
  - 错误处理

#### 4. 消息显示优化
- 文本消息只显示文字内容
- 语音消息显示语音条和文字内容
- 用户消息使用绿色背景，机器人消息使用白色背景

### 后端修改

#### 1. 新增API端点 (backend/app/api/endpoints/assistant.py)
```python
@router.post("/send-text-message")
async def send_text_message(request: Dict[str, Any], ...)
```
- 接收文本消息、场景ID、用户ID、会话ID和历史消息
- 调用服务层处理文本消息
- 返回机器人回复（包含文字和语音）

#### 2. 新增服务方法 (backend/app/services/assistant_service.py)
```python
def process_text_message(self, text: str, scene_id: int, user_id: str, conversation_id: str, history_messages: Optional[List[Dict[str, Any]]] = None)
```
- 处理用户发送的文本消息
- 使用AI生成回复
- 生成语音文件
- 返回完整的回复信息

## 功能特点

### 1. 无缝切换
- 用户可以随时在语音和文字模式间切换
- 切换按钮有明显的视觉反馈

### 2. 完整的对话上下文
- 文本消息处理时传递完整的历史消息
- AI能够基于完整对话上下文生成回复

### 3. 统一的用户体验
- 无论使用语音还是文字，都能获得机器人的语音回复
- 消息显示格式统一

### 4. 错误处理
- 完善的错误处理机制
- 用户友好的错误提示

## 使用流程

1. **语音模式**（默认）：
   - 点击🎤按钮切换到语音模式
   - 按住"按住说话"按钮录音
   - 松开发送语音消息

2. **文字模式**：
   - 点击⌨️按钮切换到文字模式
   - 在输入框中输入文字
   - 点击"发送"按钮或按回车键发送

3. **机器人回复**：
   - 无论用户使用哪种模式，机器人都以语音+文字形式回复
   - 可以点击语音条播放语音

## 技术实现要点

### 1. 状态管理
- 使用`inputMode`控制当前输入模式
- 使用`isRobotLoading`防止重复发送

### 2. 消息格式
- 统一的消息格式，支持语音和文字
- 根据消息类型决定显示方式

### 3. API设计
- 新增专门的文本消息处理接口
- 保持与现有语音接口的一致性

### 4. 样式设计
- 响应式设计，适配不同屏幕尺寸
- 模仿微信的视觉风格
- 良好的交互反馈

## 注意事项

1. 确保后端服务正常运行
2. 检查语音合成和AI服务的配置
3. 测试不同场景下的消息处理
4. 验证错误处理机制

## 扩展建议

1. 可以添加表情符号支持
2. 考虑添加图片发送功能
3. 可以添加消息撤回功能
4. 考虑添加消息搜索功能 