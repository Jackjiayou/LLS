<template>
	<view class="container">
		<!-- 头部信息 -->
		<view class="chat-header">
			<text class="scene-name">{{sceneName}}</text>
			<button class="end-btn" @click="endPractice">结束 </button>
		</view>
		
		<!-- 聊天消息区域 -->
		<scroll-view class="chat-messages" :scroll-y="true" :scroll-into-view="'msg-' + messages.length" :scroll-with-animation="true" ref="chatScroll">
			<view v-for="(msg, index) in messages" :key="index" :id="'msg-' + (index + 1)" class="message-item" :class="{ 'robot': msg.from === 'robot', 'user': msg.from === 'user' }">
				<view class="message-avatar">
					<image :src="msg.from === 'customer' ? `${apiBaseUrl}/uploads/static/robot-avatar.png` : `${apiBaseUrl}/uploads/static/user-avatar.png`"></image>
				</view>
				<view class="message-content">  
					<!-- 语音消息部分 -->
					<view class="voice-message-container">
						<!-- 只渲染假语音条动画 -->
						<template v-if="msg.isLoading">
							<view class="voice-message loading-voice-bar" :style="{ width: calculateVoiceWidth(3) }">
								<view class="voice-icon loading-voice-icon">
									<span></span> 
								</view>
								<view class="voice-duration">...</view>
							</view>
						</template>
						<template v-else>
							<view class="voice-message" :style="{ width: calculateVoiceWidth(msg.duration) }" @click="playVoice(msg.voiceUrl, index)">
								<view class="voice-icon" :class="{ 'playing': msg.isPlaying }">
									<span></span>
								</view>
								<view class="voice-duration">{{msg.duration}}''</view>
							</view>
						</template>
					</view>
					
					<!-- 文字内容部分（假语音条不显示） -->
					<template v-if="!msg.isLoading">
						<view class="text-content-container">
							<!-- 文字转录 -->
							<view class="text-transcript">
								<text>{{msg.text}}</text>
							</view>
							
							<!-- 改进建议（仅用户消息显示） -->
							<view v-if="msg.from === 'user'" class="suggestion-wrapper">
								<view class="suggestion-btn" :class="{'retry-btn': msg.suggestionError}" @click="handleSuggestionClick(msg, index)">
									<template v-if="msg.suggestionLoading">
										<text>正在生成改进建议</text>
										<text class="loading-dot">...</text>
									</template>
									<template v-else-if="msg.suggestionError">
										<text>重新生成建议</text>
										<text class="retry-icon">↻</text>
									</template>
									<template v-else>
										<text>{{msg.showSuggestion ? '收起表达建议' : '查看表达建议'}}</text>
									</template>
								</view>
								<view class="suggestion-content" v-if="msg.showSuggestion">
									<view class="suggestion-title">表达建议</view>
									<text class="suggestion-text">{{msg.suggestion}}</text>
								</view>
							</view>
						</view>
					</template>
				</view>
			</view>
		</scroll-view>
		
		<!-- 底部语音输入区域 -->
		<view class="input-area">
			<button 
				class="voice-btn" 
				:class="{ 'recording': isRecording, 'disabled': isRobotLoading }"
				@touchstart="handleTouchStart" 
				@touchend="handleTouchEnd"
				@touchcancel="handleTouchCancel">
				{{ isRecording ? '松开发送' : (isRobotLoading ? '顾客正在输入...' : '按住说话') }}
			</button>
		</view>
		
		<!-- 录音提示浮层 -->
		<view class="recording-overlay" v-if="showRecordingOverlay">
			<view class="recording-content">
				<view class="recording-icon-wrapper">
					<view class="recording-icon" :class="{ 'recording-animation': isRecording }"></view>
				</view>
				<view class="recording-text">{{recordingTipText}}</view>
				<view class="recording-time" v-if="isRecording">{{recordingTime}}s</view>
			</view>
		</view>
		
		<!-- 结束确认对话框 -->
		<view class="dialog-mask" v-if="showEndDialog">
			<view class="dialog-container new-dialog">
				<view class="dialog-close" @click="closeEndDialog">×</view>
				<view class="dialog-icon">
					<image src="/static/dialog-bubble.png" mode="aspectFit" />
				</view>
				<view class="dialog-title new-dialog-title">你确定要结束这次练习吗？</view>
				<view class="dialog-buttons new-dialog-buttons">
					<button class="dialog-btn dialog-btn-primary" @click="endAndViewReport">结束对话，并查看测评报告</button>
					<button class="dialog-btn dialog-btn-outline" @click="endOnly">结束对话</button>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import config from '@/config.js'
	import request from '@/utils/request.js'
	import { v4 as uuidv4 } from 'uuid'
	
	export default {
		data() {
			return {
				sceneId: 0,
				sceneName: '',
				messages: [],
				isRecording: false,
				showEndDialog: false,
				recorderManager: null, // 录 音管理器
				currentVoicePath: '', // 当前录音文件路径
				// 用户信息
				userId: '', // 用户ID
				username: '', // 用户名
				conversationId: '', // 对话ID
				// 新增: 机器人消息加载标志
				isRobotLoading: false,
				// API地址配置
				apiBaseUrl: config.apiBaseUrl, // 修改为您的实际API地址 ai.dl-dd.com

				// 录音相关
				showRecordingOverlay: false, // 是否显示录音提示浮层
				recordingTipText: '准备录音...', // 录音提示文本
				recordingTime: 0, // 录音时长（秒）
				recordingTimer: null, // 录音计时器
				// 音频播放相关
				currentAudioContext: null, // 当前播放的音频上下文
				currentPlayingIndex: -1, // 当前正在播放的消息索引
				// 语音条宽度配置
				minVoiceWidth: 120, // 最小宽度（rpx）
				maxVoiceWidth: 400, // 最大宽度（rpx）
				
			}
		},
		created() {
			// 从本地存储获取用户ID
			this.userId = uni.getStorageSync('userId') || '';
		},
		onLoad(options) {
			if (options.sceneId) {
				this.sceneId = parseInt(options.sceneId);
				// 获取用户信息
				const userInfo = uni.getStorageSync('userInfo');
				if (userInfo) {
					this.userId = userInfo.userId;
					this.username = userInfo.nickname;
				} else {
					// 如果没有用户信息，跳转到登录页
					uni.showToast({
						title: '请先登录',
						icon: 'none',
						duration: 2000
					});
					setTimeout(() => {
						uni.reLaunch({
							url: '/pages/login/login'
						});
					}, 2000);
					return;
				}
				
                console.log('创建对话onload')
				// 每次进入页面时生成新的会话ID
				this.startNewConversation();
				this.startNewPractice();
				this.getSceneInfo();
				// 初始化录音管理器
				this.initRecorder();
				
				// 添加初始机器人消息加载效果
				this.messages.push({
					from: 'customer',
					text: '机器人正在回复...',
					voiceUrl: '',
					duration: '',
					isPlaying: false,
					isLoading: true,
					timestamp: new Date().toISOString()
				});
				this.isRobotLoading = true;  // 设置机器人加载标志
				
				// 从后端获取机器人首次问候
				this.getRobotMessage();
			}
		},
		methods: {
            // 开始新练习
            // 开始新练习
            async startNewPractice() {
                try {
                    // 确保 sceneId 和 userId 是数字类型
                    const sceneId = parseInt(this.sceneId);
                    const userId = parseInt(this.userId);
                    
                    console.log('开始练习参数:', { sceneId, userId });
                    
                    const response = await request({
                        url: '/conversation/practice/start',
                        method: 'POST',
                        data: {
                            sceneId: sceneId,
                            userId: userId
                        },
                        header: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (response.data && response.data.practice_id) {
                        this.practiceId = response.data.practice_id;
                        this.isPracticeActive = true;
                        console.log('练习开始，ID:', this.practiceId);
                    }
                } catch (error) {
                    console.error('开始练习失败:', error);
                    // 显示错误提示
                    uni.showModal({
                        title: '提示',
                        content: '开始对话失败，是否重新开始？',
                        confirmText: '重新开始',
                        cancelText: '返回首页',
                        success: (res) => {
                            if (res.confirm) {
                                // 用户点击重新开始，重新加载页面
                                uni.reLaunch({
                                    url: `/pages/chat/chat?sceneId=${this.sceneId}`
                                });
                            } else {
                                // 用户点击返回首页
                                uni.navigateBack({
                                    delta: 2  // 返回上上页
                                });
                            }
                        }
                    });
                }
            },
            
            // 保存消息到练习记录
            async saveMessageToPractice(message) {
                if (!this.isPracticeActive || !this.practiceId) return;
                
                try {
                    await request({
                        url: '/conversation/practice/message',
                        method: 'POST',
                        data: {
                            practice_id: this.practiceId,
                            message: {
                                from: message.from,
                                text: message.text,
                                voiceUrl: message.voiceUrl,
                                duration: message.duration,
                                suggestion: message.suggestion,
                                timestamp: message.timestamp
                            }
                        }
                    });
                } catch (error) {
                    console.error('保存消息失败:', error);
                }
            },
            
            // 修改现有的 endPractice 方法
            async endPractice() {
                if (!this.isPracticeActive || !this.practiceId) return;
                
                try {
                    await request({
                        url: '/conversation/practice/end',
                        method: 'POST',
                        data: {
                            practice_id: this.practiceId
                        }
                    });
                    
                    this.isPracticeActive = false;
                    this.showEndDialog = true;
                } catch (error) {
                    console.error('结束练习失败:', error);
                    uni.showToast({
                        title: '结束练习失败',
                        icon: 'none'
                    });
                }
            },
            
            // 格式化并发送聊天记录
            async saveChatHistory() {
                try {
                    // 过滤掉加载中的消息
                    const realMessages = this.messages.filter(msg => !msg.isLoading);
                    
                    // 格式化消息为指定格式
                    const formattedMessages = realMessages.map(msg => ({
                        from: msg.from,
                        text: msg.text,
                        voiceUrl: msg.voiceUrl || '',
                        duration: parseInt(msg.duration) || 0,
                        suggestion: msg.suggestion || '',
                        timestamp: msg.timestamp || new Date().toISOString()
                    }));
        
                    // 发送到后端
                    const response = await request({
                        url: '/conversation/practice/save-json-message',
                        method: 'POST',
                        data: {
                            practice_id: this.practiceId,
                            chat_history: formattedMessages
                        },
                        header: {
                            'Content-Type': 'application/json'
                        }
                    });
        
                    if (response.data && response.data.success) {
                        console.log('聊天记录保存成功');
                    } else {
                        console.error('聊天记录保存失败:', response.data);
                    }
                } catch (error) {
                    console.error('保存聊天记录时发生错误:', error);
                }
            },
            
			// 开始新会话
			startNewConversation() {
				this.conversationId = uuidv4();
				this.messages = [];
				// 保存新的会话ID
				uni.setStorageSync('currentConversationId', this.conversationId);
				console.log('新会话ID:', this.conversationId);
			},

			getSceneInfo() {
				// 获取场景名称
				const sceneNames = {
					0: '核苷酸介绍',
					1: '新客户开发',
					2: '异议处理',
					3: '产品推荐',
					4: '成交技巧'
				};
				this.sceneName = sceneNames[this.sceneId] || '未知场景';
				
				// 实际项目中应该从API获取
				// uni.request({
				//   url: `http://your-api-url/scenes/${this.sceneId}`,
				//   success: (res) => {
				//     this.sceneName = res.data.name;
				//   }
				// });
			},
			// 预下载音频文件
			preDownloadVoice(voiceUrl) {
				if (!voiceUrl || !voiceUrl.startsWith('http')) return;
				uni.downloadFile({
					url: voiceUrl,
					success: (res) => {
						if (res.statusCode === 200) {
							const idx = this.messages.findIndex(msg => msg.voiceUrl === voiceUrl);
							if (idx !== -1) {
								this.$set(this.messages[idx], 'voiceUrl', res.tempFilePath);
							}
						}
					}
				});
			},
			// 获取机器人消息
			async getRobotMessage() {
				try {
					this.isRobotLoading = true;
					
					const realMessages = this.messages.filter(msg => !(msg.from === 'customer' && msg.isLoading));
					const response = await request({
						url: '/conversation/get-robot-message',
						method: 'GET',
						data: {
							sceneId: this.sceneId,
							messageCount: realMessages.length,
							messages: JSON.stringify(realMessages.map(msg => ({
								from: msg.from,
								text: msg.text
							}))),
							userId: this.userId,
							username: this.username,
							conversationId: this.conversationId
						},
						header: {
							'Content-Type': 'application/json'
						}
					});
					if (response.statusCode === 200 && response.data) {
						// 2. 替换第一个 isLoading: true 的机器人消息为真实消息
						const idx = this.messages.findIndex(msg => msg.from === 'customer' && msg.isLoading);
						const realMsg = {
							from: 'customer',
							text: response.data.text,
							voiceUrl: response.data.voiceUrl,
							duration: response.data.duration,
							timestamp: new Date().toISOString(),
							isPlaying: false
						};
						if (idx !== -1) {
							this.$set(this.messages, idx, realMsg);
						} else {
							this.messages.push(realMsg);
						}
						// 预下载机器人语音
						if (response.data.voiceUrl) {
							this.preDownloadVoice(response.data.voiceUrl);
						}
						this.$nextTick(() => {
							this.scrollToBottom();
							// 设置机器人消息加载标志为false
							this.isRobotLoading = false;
						});
					} else {
						// 获取失败时移除假语音条
						const idx = this.messages.findIndex(msg => msg.from === 'customer' && msg.isLoading);
						if (idx !== -1) this.messages.splice(idx, 1);
						console.error('获取机器人消息失败:', response);
						uni.showToast({
							title: '获取消息失败',
							icon: 'none'
						});
						// 设置机器人消息加载标志为false
						this.isRobotLoading = false;
					}
				} catch (error) {
					// 获取失败时移除假语音条
					const idx = this.messages.findIndex(msg => msg.from === 'customer' && msg.isLoading);
					if (idx !== -1) this.messages.splice(idx, 1);
					console.error('获取机器人消息失败:', error);
					uni.showToast({
						title: '获取消息失败',
						icon: 'none'
					});
					// 设置机器人消息加载标志为false
					this.isRobotLoading = false;
				}
			},
			// 初始化录音管理器
			initRecorder() {
				this.recorderManager = uni.getRecorderManager();
				
				// 监听录音结束事件
				this.recorderManager.onStop((res) => {
					console.log('录音结束事件触发:', res);
					if (res.tempFilePath) {
						this.currentVoicePath = res.tempFilePath;
						this.sendVoiceMessage(res.tempFilePath, res.duration);
					}
				});
				
				// 监听录音错误事件
				this.recorderManager.onError((res) => {
					console.error('录音失败:', res);
					uni.showToast({
						title: '录音失败',
						icon: 'none'
					});
					this.isRecording = false;
				});
			},
			// 开始录音
			startRecording() {
				this.isRecording = true;
				this.showRecordingOverlay = true;
				this.recordingTipText = '正在录音...';
				this.recordingTime = 0;
				
				// 开始计时
				this.recordingTimer = setInterval(() => {
					this.recordingTime++;
					
					// 超过60秒自动停止
					if (this.recordingTime >= 60) {
						this.stopRecording();
						uni.showToast({
							title: '录音已达最大时长',
							icon: 'none'
						});
					}
				}, 1000);
				
				// 检查录音权限
				uni.authorize({
					scope: 'scope.record',
					success: () => {
						// 开始录音
						const options = {
							duration: 60000, // 最长录音时间，单位ms，最大可设置为60s
							sampleRate: 16000, // 采样率
							numberOfChannels: 1, // 录音通道数
							encodeBitRate: 96000, // 编码码率
							format: 'mp3', // 修改为mp3格式，兼容性更好
							frameSize: 50 // 指定帧大小，单位KB
						};
						
						console.log('开始录音...');
						this.recorderManager.start(options);
					},
					fail: () => {
						console.error('未授权录音权限');
						this.recordingTipText = '需要录音权限';
						setTimeout(() => {
							this.showRecordingOverlay = false;
							this.isRecording = false;
							clearInterval(this.recordingTimer);
						}, 1500);
						
						uni.showModal({
							title: '提示',
							content: '需要您授权录音权限才能发送语音消息',
							confirmText: '去授权',
							success: (res) => {
								if (res.confirm) {
									uni.openSetting();
								}
							}
						});
					}
				});
			},
			// 处理按钮触摸开始事件
			handleTouchStart() {
				if (!this.isRobotLoading) {
					this.startRecording();
				}
			},
			
			// 处理按钮触摸结束事件
			handleTouchEnd() {
				if (this.isRecording) {
					this.stopRecording();
				}
			},
			
			// 处理按钮触摸取消事件
			handleTouchCancel() {
				if (this.isRecording) {
					this.cancelRecording();
				}
			},
			// 结束录音
			stopRecording() {
				if (!this.isRecording) return;
				
				console.log('结束录音');
				this.isRecording = false;
				this.recordingTipText = '发送中...';
				
				// 清除计时器
				clearInterval(this.recordingTimer);
				
				// 停止录音
				this.recorderManager.stop();
				
				// 延迟关闭提示浮层
				setTimeout(() => {
					this.showRecordingOverlay = false;
				}, 1000);
			},
			// 取消录音
			cancelRecording() {
				console.log('取消录音');
				this.isRecording = false;
				this.recordingTipText = '已取消';
				
				// 清除计时器
				clearInterval(this.recordingTimer);
				
				// 停止录音
				this.recorderManager.stop();
				
				// 延迟关闭提示浮层
				setTimeout(() => {
					this.showRecordingOverlay = false;
				}, 1000);
			},
			// 发送语音消息
			sendVoiceMessage(voicePath, duration) {
				console.log('发送语音消息:', voicePath, duration);
				
				// 计算语音时长（秒）
				const durationInSeconds = Math.ceil(duration / 1000);
				
				// 上传语音到服务器并获取文本转写
				this.uploadVoiceAndGetText(voicePath, durationInSeconds);
			},
			// 上传语音并获取文本转写
			uploadVoiceAndGetText(voicePath, duration) {
				//uni.showLoading({ title: '转写分析中...' });
				const timestamp = new Date().getTime();
				const randomStr = Math.random().toString(36).substring(2, 8);
				const fileName = `audio_${timestamp}_${randomStr}.mp3`;

				// 1. 立即插入占位消息
				const userMessageIndex = this.messages.length;
				this.messages.push({
					from: 'user',
					text: '语音识别中...',
					voiceUrl: voicePath, // 本地临时文件
					duration: '',
					suggestion: '',
					polishedText: '',
					showSuggestion: false,
					isPlaying: false,
					suggestionLoading: false,
					suggestionError: false,
					isLoading: true
				});
				this.scrollToBottom();

				uni.uploadFile({
					url: `${this.apiBaseUrl}/conversation/speech-to-text`,
					filePath: voicePath,
					name: 'audio_file',
					formData: {
						userId: this.userId,
						username: this.username,
						conversationId: this.conversationId,
						sceneId: this.sceneId,
						fileName: fileName
					},

					header: {
						'Authorization': `Bearer ${uni.getStorageSync('token')}`
					},

					success: (uploadRes) => {
						try {
							const data = JSON.parse(uploadRes.data);
							if (data.text) {
								// 2. 替换占位消息内容为真实内容
								this.$set(this.messages, userMessageIndex, {
									from: 'user',
									text: data.text,
									voiceUrl: data.voiceUrl || voicePath,
									duration: duration.toString(),
									suggestion: '',
									polishedText: '',
									showSuggestion: false,
									isPlaying: false,
									suggestionLoading: true,
									suggestionError: false,
									isLoading: false
								});
								// 预下载用户语音
								if (data.voiceUrl) {
									this.preDownloadVoice(data.voiceUrl);
								}
								this.scrollToBottom();
								// 并行获取建议和机器人回复
								
								// 立即插入假机器人语音条
								this.messages.push({
									from: 'customer',
									text: '机器人正在回复...',
									voiceUrl: '',
									duration: '',
									isPlaying: false,
									isLoading: true,
									timestamp: new Date().toISOString()
								});
								this.isRobotLoading = true;  // 设置机器人加载标志
								this.getRobotMessage();
								this.getMessageSuggestion(data.text, userMessageIndex);
								
							} else {
								// 语音识别失败，移除假语音条
								this.messages.splice(userMessageIndex, 1);
								uni.showToast({ title: '语音识别失败', icon: 'none' });
							}
						} catch (e) {
							// 解析失败，移除假语音条
							this.messages.splice(userMessageIndex, 1);
							console.error('解析语音识别结果失败:', e);
							uni.showToast({ title: '语音识别失败', icon: 'none' });
						}
					},
					fail: (err) => {
						// 上传失败，移除假语音条
						this.messages.splice(userMessageIndex, 1);
						console.error('上传语音失败:', err);
						uni.showToast({ title: '上传语音失败', icon: 'none' });
					},
					complete: () => { uni.hideLoading(); }
				});
			},
			// 获取消息改进建议
			getMessageSuggestion(text, messageIndex) {
				const realMessages = this.messages.filter(msg => !(msg.from === 'customer' && msg.isLoading));
				this.$set(this.messages[messageIndex], 'suggestionLoading', true);
				this.$set(this.messages[messageIndex], 'suggestionError', false);
				
				request({
					url: '/conversation/analyze',
					method: 'POST',
					data: {
						messages_all: JSON.stringify(realMessages.map(msg => ({
							from: msg.from,
							text: msg.text
						}))),
						sceneId: this.sceneId,
						message: text,
						userId: this.userId,
						conversationId: this.conversationId
					},
					header: {
						'Content-Type': 'application/json'
					}
				}).then(res => {
					if (res.data && res.data.suggestion) {
						this.$set(this.messages[messageIndex], 'suggestion', res.data.suggestion);
						this.$set(this.messages[messageIndex], 'suggestionLoading', false);
						this.$set(this.messages[messageIndex], 'suggestionError', false);
					} else {
						this.$set(this.messages[messageIndex], 'suggestionLoading', false);
						this.$set(this.messages[messageIndex], 'suggestionError', true);
					}
				}).catch(err => {
					this.$set(this.messages[messageIndex], 'suggestionLoading', false);
					this.$set(this.messages[messageIndex], 'suggestionError', true);
				});
			},
			// 获取润色表达
			getPolishedText(text, messageIndex) {
				request({
					url: '/polish-text',
					method: 'POST',
					data: {
						text: text,
						sceneId: this.sceneId,
						userId: this.userId,
						conversationId: this.conversationId
					}
				}).then(res => {
					if (res.data && res.data.polishedText) {
						this.$set(this.messages[messageIndex], 'polishedText', res.data.polishedText);
					}
				}).catch(err => {
					console.error('获取润色表达失败:', err);
					this.$set(this.messages[messageIndex], 'polishedText', '润色表达生成失败，请稍后再试');
				});
			},
			// 格式化消息用于分析
			formatMessagesForAnalysis() {
				return this.messages.map(msg => ({
					role: msg.from === 'user' ? 'user' : 'customer',
					content: msg.text
				}));
			},
			// 滚动到底部
			scrollToBottom() {
				this.$nextTick(() => {
					const query = uni.createSelectorQuery().in(this);
					query.select('.chat-messages').boundingClientRect(data => {
						if (data) {
							uni.pageScrollTo({
								scrollTop: data.height,
								duration: 300
							});
						}
					}).exec();
				});
			},
			// 播放语音
			playVoice(voiceUrl, index) {
				console.log('播放语音', voiceUrl);
				
				// 检查URL是否有效
				if (!voiceUrl) {
					uni.showToast({
						title: '无效的语音文件',
						icon: 'none'
					});
					return;
				}
				
				// 如果点击的是当前正在播放的语音，则停止播放
				if (this.currentPlayingIndex === index) {
					try {
						this.currentAudioContext.stop();
						this.currentAudioContext.destroy();
						this.currentAudioContext = null;
						this.$set(this.messages[index], 'isPlaying', false);
						this.currentPlayingIndex = -1;
					} catch (e) {
						console.error('停止当前音频失败:', e);
					}
					return;
				}
				
				// 如果当前有音频在播放，先停止
				if (this.currentAudioContext) {
					try {
						this.currentAudioContext.stop();
						this.currentAudioContext.destroy();
					} catch (e) {
						console.error('停止当前音频失败:', e);
					}
					
					// 重置之前播放的消息状态
					if (this.currentPlayingIndex >= 0 && this.currentPlayingIndex < this.messages.length) {
						this.$set(this.messages[this.currentPlayingIndex], 'isPlaying', false);
					}
				}
				
				// 设置当前消息为播放状态
				this.$set(this.messages[index], 'isPlaying', true);
				this.currentPlayingIndex = index;
				
				// 创建音频上下文
				this.currentAudioContext = uni.createInnerAudioContext();
				
				// 设置音频源
				if (voiceUrl.startsWith('http')) {
					// 如果是网络URL，先下载到本地再播放
					console.log('下载并播放网络音频:', voiceUrl);
					
					// 下载音频文件
					uni.downloadFile({
						url: voiceUrl,
						success: (res) => {
							console.log('音频下载成功:', res);
							if (res.statusCode === 200) {
								// 下载成功，使用本地路径播放
								this.currentAudioContext.src = res.tempFilePath;
								console.log('使用下载的本地文件播放:', res.tempFilePath);
				
				// 监听播放开始
				this.currentAudioContext.onPlay(() => {
					console.log('开始播放');
				});
				
				// 监听播放错误
				this.currentAudioContext.onError((err) => {
					console.error('播放错误:', err);
					console.error('播放失败的URL:', voiceUrl);
					
					// 重置播放状态
					this.$set(this.messages[index], 'isPlaying', false);
					this.currentPlayingIndex = -1;
					
					// 释放资源
					try {
						this.currentAudioContext.destroy();
						this.currentAudioContext = null;
					} catch (e) {
						console.error('销毁音频上下文失败:', e);
					}
				});
				
				// 监听播放结束
				this.currentAudioContext.onEnded(() => {
					console.log('播放结束');
					// 重置播放状态
					this.$set(this.messages[index], 'isPlaying', false);
					this.currentPlayingIndex = -1;
					
					// 释放资源
					try {
						this.currentAudioContext.destroy();
						this.currentAudioContext = null;
					} catch (e) {
						console.error('销毁音频上下文失败:', e);
					}
				});
				
				// 开始播放
				try {
					this.currentAudioContext.play();
				} catch (e) {
					console.error('播放音频失败:', e);
					// 重置播放状态
					this.$set(this.messages[index], 'isPlaying', false);
					this.currentPlayingIndex = -1;
				}
					} else {
								console.error('下载失败，状态码:', res.statusCode);
								
								// 重置播放状态
								this.$set(this.messages[index], 'isPlaying', false);
								this.currentPlayingIndex = -1;
						}
					},
					fail: (err) => {
							console.error('下载失败:', err);
							
							// 重置播放状态
						this.$set(this.messages[index], 'isPlaying', false);
						this.currentPlayingIndex = -1;
						}
					});
				} else {
					// 如果是本地临时文件，先检查文件是否存在
					uni.getFileInfo({
						filePath: voiceUrl,
						success: () => {
							this.currentAudioContext.src = voiceUrl;
							console.log('使用本地文件播放:', voiceUrl);
				
				// 监听播放开始
				this.currentAudioContext.onPlay(() => {
					console.log('开始播放');
				});
				
				// 监听播放错误
				this.currentAudioContext.onError((err) => {
					console.error('播放错误:', err);
					console.error('播放失败的URL:', voiceUrl);
					
					// 重置播放状态
					this.$set(this.messages[index], 'isPlaying', false);
					this.currentPlayingIndex = -1;
					
					// 释放资源
					try {
						this.currentAudioContext.destroy();
						this.currentAudioContext = null;
					} catch (e) {
						console.error('销毁音频上下文失败:', e);
					}
				});
				
				// 监听播放结束
				this.currentAudioContext.onEnded(() => {
					console.log('播放结束');
					// 重置播放状态
					this.$set(this.messages[index], 'isPlaying', false);
					this.currentPlayingIndex = -1;
					
					// 释放资源
					try {
						this.currentAudioContext.destroy();
						this.currentAudioContext = null;
					} catch (e) {
						console.error('销毁音频上下文失败:', e);
					}
				});
				
				// 开始播放
				try {
					this.currentAudioContext.play();
				} catch (e) {
					console.error('播放音频失败:', e);
					// 重置播放状态
					this.$set(this.messages[index], 'isPlaying', false);
					this.currentPlayingIndex = -1;
				}
			},
						fail: () => {
							console.error('文件不存在:', voiceUrl);
							
							// 重置播放状态
							this.$set(this.messages[index], 'isPlaying', false);
							this.currentPlayingIndex = -1;
						}
					});
				}
			},
			toggleSuggestion(index) {
				// 切换显示/隐藏建议
				this.$set(this.messages[index], 'showSuggestion', !this.messages[index].showSuggestion);
			},
			sendMessageToBackend(text) {
				// 发送消息到后端进行分析
				console.log('发送消息到后端分析:', text);
				// 实际项目中应该使用API请求
				// uni.request({
				//   url: 'http://your-api-url/analyze',
				//   method: 'POST',
				//   data: {
				//     sceneId: this.sceneId,
				//     message: text,
				//     allMessages: this.messages
				//   },
				//   success: (res) => {
				//     console.log('分析结果:', res.data);
				//   }
				// });
			},
			endPractice() {
				this.showEndDialog = true;
			},
			closeEndDialog() {
				this.showEndDialog = false;
			},
			endOnly() {
                console.log('调用saveChatHistory')
                this.saveChatHistory()
				// 结束对话，返回首页
				uni.navigateBack({
					delta: 2 // 返回上上页
				});
			},
			endAndViewReport() {
				// 发送所有对话记录到后端生成报告
				this.generateReport();
				// 跳转到新版报告页面
				uni.navigateTo({
					url: `/pages/report/report?sceneId=${this.sceneId}`
				});
			},
			generateReport() {
				console.log('生成练习报告...');
				
				request({
					url: '/report',
					method: 'POST',
					data: {
						sceneId: this.sceneId,
						userId: this.userId,
						conversationId: this.conversationId,
						messages: this.formatMessagesForAnalysis()
					}
				}).then(res => {
					console.log('报告生成成功:', res.data);
					if (res.data && res.data.reportId) {
						uni.setStorageSync('latestReportId', res.data.reportId);
					}
				}).catch(err => {
					console.error('报告生成失败:', err);
					uni.showToast({
						title: '报告生成失败',
						icon: 'none'
					});
				});
			},
			// 计算语音条宽度
			calculateVoiceWidth(duration) {
				// 将时长转换为数字
				const durationNum = parseInt(duration) || 0;
				
				// 根据时长计算宽度，时长越长宽度越大
				// 这里使用一个简单的线性映射，可以根据需要调整
				let width = this.minVoiceWidth + (durationNum / 60) * (this.maxVoiceWidth - this.minVoiceWidth);
				
				// 确保宽度在最小和最大值之间
				width = Math.max(this.minVoiceWidth, Math.min(width, this.maxVoiceWidth));
				
				return width + 'rpx';
			},
			// 处理建议按钮点击
			handleSuggestionClick(msg, index) {
				if (msg.suggestionError) {
					// 如果是错误状态，重新生成建议
					this.$set(this.messages[index], 'suggestionLoading', true);
					this.$set(this.messages[index], 'suggestionError', false);
					this.getMessageSuggestion(msg.text, index);
				} else {
					// 否则切换显示/隐藏
					this.toggleSuggestion(index);
				}
			}
		}
        
        
	}
</script>

<style>
	.container {
		display: flex;
		flex-direction: column;
		height: 100vh;
		background-color: #f5f5f5;
	}
	
	.chat-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 20rpx 30rpx;
		background-color: #fff;
		border-bottom: 1rpx solid #eee;
	}
	
	.scene-name {
		font-size: 32rpx;
		font-weight: bold;
	}
	
	.end-btn {
		font-size: 28rpx;
		background-color: #10b981;
		color: #fff;
		padding: 10rpx 30rpx;
		border-radius: 30rpx;
		line-height: 1.5;
	}
	
	.chat-messages {
		flex: 1;
		padding: 20rpx;
		overflow-y: auto;
	}
	
	.message-item {
		display: flex;
		margin-bottom: 30rpx;
	}
	
	.robot {
		flex-direction: row;
	}
	
	.user {
		flex-direction: row-reverse;
	}
	
	.message-avatar {
		width: 80rpx;
		height: 80rpx;
		margin: 0 20rpx;
	}
	
	.message-avatar image {
		width: 100%;
		height: 100%;
		border-radius: 50%;
	}
	
	.message-content {
		max-width: 70%;
		display: flex;
		flex-direction: column;
	}
	
	.voice-message-container {
		margin-bottom: 15rpx;
	}
	
	.robot .voice-message-container {
		align-self: flex-start;
	}
	
	.user .voice-message-container {
		align-self: flex-end;
	}
	
	.voice-message {
		display: flex;
		align-items: center;
		padding: 15rpx 20rpx;
		border-radius: 8rpx;
		background-color: #fff;
		width: fit-content;
		min-width: 120rpx;
		transition: width 0.3s ease;
		position: relative;
	}
	
	.user .voice-message {
		flex-direction: row-reverse;
		background-color: #95EC69;
	}
	
	.voice-icon {
		width: 40rpx;
		height: 40rpx;
		margin-right: 10rpx;
		position: relative;
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	
	.user .voice-icon {
		margin-right: 0;
		margin-left: 10rpx;
	}
	
	.voice-icon::before,
	.voice-icon::after,
	.voice-icon span {
		content: '';
		width: 4rpx;
		height: 16rpx;
		background: #666;
		border-radius: 4rpx 4rpx 0 0;
		transform-origin: bottom;
	}
	
	.user .voice-icon::before,
	.user .voice-icon::after,
	.user .voice-icon span {
		background: #666;
	}
	
	.voice-icon.playing::before,
	.voice-icon.playing::after,
	.voice-icon.playing span {
		animation: voice-wave 1.5s ease-in-out infinite;
	}
	
	.voice-icon.playing::before {
		animation-delay: 0s;
	}
	
	.voice-icon.playing span {
		animation-delay: 0.2s;
	}
	
	.voice-icon.playing::after {
		animation-delay: 0.4s;
	}
	
	@keyframes voice-wave {
		0%, 100% {
			transform: scaleY(1);
		}
		50% {
			transform: scaleY(1.5);
		}
	}
	
	.robot .voice-icon {
		filter: brightness(0) saturate(100%) invert(40%) sepia(82%) saturate(1644%) hue-rotate(199deg) brightness(97%) contrast(101%);
	}
	
	.robot .voice-icon.playing {
		animation: voice-wave 1.5s ease-in-out infinite;
		transform-origin: center;
	}
	
	.voice-duration {
		font-size: 24rpx;
		color: #666;
	}
	
	.user .voice-duration {
		margin-right: 10rpx;
		color: #666;
	}
	
	.robot .voice-duration {
		color: #666;
	}
	
	.text-content-container {
		background-color: #fff;
		border-radius: 12rpx;
		padding: 15rpx;
		box-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.1);
	}
	
	.robot .text-content-container {
		background-color: #fff;
		color: #333;
	}
	
	.text-transcript {
		font-size: 28rpx;
		line-height: 1.4;
	}
	
	.robot .text-transcript {
		color: #333;
	}
	
	.suggestion-wrapper {
		margin-top: 15rpx;
		border-top: 1rpx dashed #ddd;
		padding-top: 15rpx;
	}
	
	.robot .suggestion-wrapper {
		border-top: 1rpx dashed rgba(255, 255, 255, 0.3);
	}
	
	.suggestion-btn {
		display: inline-block;
		font-size: 24rpx;
		color: #007AFF;
		background-color: rgba(0, 122, 255, 0.1);
		padding: 6rpx 15rpx;
		border-radius: 20rpx;
	}
	
	.robot .suggestion-btn {
		color: #fff;
		background-color: rgba(255, 255, 255, 0.2);
	}
	
	.suggestion-content {
		margin-top: 10rpx;
		padding: 15rpx;
		background-color: #f9f9f9;
		border-radius: 8rpx;
		border-left: 6rpx solid #007AFF;
	}
	
	.robot .suggestion-content {
		background-color: rgba(255, 255, 255, 0.1);
		border-left: 6rpx solid #fff;
	}
	
	.suggestion-title {
		font-size: 24rpx;
		color: #007AFF;
		font-weight: bold;
		margin-bottom: 6rpx;
	}
	
	.robot .suggestion-title {
		color: #fff;
	}
	
	.suggestion-text {
		font-size: 26rpx;
		color: #666;
	}
	
	.robot .suggestion-text {
		color: rgba(255, 255, 255, 0.9);
	}
	
	.input-area {
		padding: 20rpx;
		background-color: #fff;
		border-top: 1rpx solid #eee;
	}
	
	.voice-btn {
		width: 100%;
		height: 90rpx;
		line-height: 90rpx;
		text-align: center;
		background-color: #f2f2f2;
		color: #333;
		border-radius: 45rpx;
		font-size: 30rpx;
	}
	
	.recording {
		background-color: #e0e0e0;
	}
	
	/* 添加禁用状态样式 */
	.voice-btn.disabled {
		background-color: #d9d9d9;
		color: #999;
		pointer-events: none;
	}
	
	.dialog-mask {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.6);
		z-index: 999;
		display: flex;
		justify-content: center;
		align-items: center;
	}
	
	.dialog-container {
		width: 80%;
		background-color: #fff;
		border-radius: 12rpx;
		overflow: hidden;
	}
	
	.dialog-title {
		padding: 40rpx 30rpx;
		text-align: center;
		font-size: 32rpx;
		border-bottom: 1rpx solid #eee;
	}
	
	.dialog-buttons {
		display: flex;
		flex-direction: column;
	}
	
	.dialog-btn {
		height: 100rpx;
		line-height: 100rpx;
		text-align: center;
		font-size: 30rpx;
		border-bottom: 1rpx solid #eee;
	}
	
	.dialog-btn:last-child {
		border-bottom: none;
	}
	
	.cancel {
		color: #999;
	}
	
	.confirm {
		color: #fff;
		background-color: #10b981;
	}
	
	.report {
		color: #fff;
		background-color: #10b981;
	}
	
	/* 录音提示浮层 */
	.recording-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.6);
		z-index: 999;
		display: flex;
		justify-content: center;
		align-items: center;
	}
	
	.recording-content {
		width: 300rpx;
		height: 300rpx;
		background-color: rgba(255, 255, 255, 0.9);
		border-radius: 20rpx;
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.2);
	}
	
	.recording-icon-wrapper {
		width: 120rpx;
		height: 120rpx;
		margin-bottom: 30rpx;
		display: flex;
		justify-content: center;
		align-items: center;
	}
	
	.recording-icon {
		width: 80rpx;
		height: 80rpx;
		background-color: #f2f2f2;
		border-radius: 50%;
		position: relative;
	}
	
	.recording-animation {
		background-color: #ff4d4f;
		animation: pulse 1.5s infinite alternate;
	}
	
	@keyframes pulse {
		0% {
			transform: scale(0.8);
			opacity: 0.8;
		}
		50% {
			transform: scale(1.2);
			opacity: 1;
		}
		100% {
			transform: scale(0.8);
			opacity: 0.8;
		}
	}
	
	.recording-text {
		font-size: 32rpx;
		color: #333;
		margin-bottom: 20rpx;
	}
	
	.recording-time {
		font-size: 28rpx;
		color: #666;
	}
	
	.loading-voice-bar {
		background: #e6f7ff;
		animation: loading-bar-blink 1.2s infinite alternate;
	}
	
	.loading-voice-icon span {
		background: #1890ff;
		animation: voice-wave 0.8s infinite linear;
	}
	
	@keyframes loading-bar-blink {
		0% { opacity: 0.7; }
		100% { opacity: 1; }
	}
	
	.loading-dot {
		display: inline-block;
		margin-left: 6rpx;
		animation: blink 1s infinite alternate;
	}
	
	@keyframes blink {
		0% { opacity: 0.3; }
		100% { opacity: 1; }
	}
	
	.new-dialog {
		border-radius: 24rpx;
		box-shadow: 0 8rpx 32rpx rgba(16,185,129,0.10);
		position: relative;
		padding-bottom: 40rpx;
		display: flex;
		flex-direction: column;
		align-items: center;
	}
	
	.dialog-close {
		position: absolute;
		top: 24rpx;
		right: 24rpx;
		width: 48rpx;
		height: 48rpx;
		border-radius: 50%;
		background: #f2f2f2;
		color: #666;
		font-size: 36rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 2;
	}
	
	.dialog-icon {
		margin-top: 48rpx;
		margin-bottom: 24rpx;
	}
	
	.dialog-icon image {
		width: 80rpx;
		height: 80rpx;
	}
	
	.new-dialog-title {
		font-size: 32rpx;
		color: #222;
		text-align: center;
		margin-bottom: 48rpx;
		font-weight: bold;
	}
	
	.new-dialog-buttons {
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: 24rpx;
		align-items: center;
	}
	
	.dialog-btn-primary {
		width: 80%;
		height: 88rpx;
		border-radius: 44rpx;
		font-size: 30rpx;
		font-weight: 500;
		background: #10b981;
		color: #fff;
		border: none;
		margin: 0 auto;
	}
	
	.dialog-btn-outline {
		width: 80%;
		height: 88rpx;
		border-radius: 44rpx;
		font-size: 30rpx;
		font-weight: 500;
		background: #fff;
		color: #10b981;
		border: 2rpx solid #10b981;
		margin: 0 auto;
	}
	
	.suggestion-btn.retry-btn {
		background-color: #fff3f0;
		color: #ff4d4f;
		border: 1rpx solid #ffccc7;
	}
	
	.retry-icon {
		margin-left: 8rpx;
		font-size: 24rpx;
		animation: rotate 1s linear infinite;
	}
	
	@keyframes rotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
</style> 