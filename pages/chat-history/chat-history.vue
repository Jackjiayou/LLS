<template>
	<view class="container">
		<!-- 头部信息 -->
		<view class="chat-header">
			<text class="scene-name">{{sceneName}}</text>
			<text class="practice-date">{{practiceDate}}</text>
		</view>
		
		<!-- 聊天消息区域 -->
		<scroll-view class="chat-messages" :scroll-y="true" :scroll-into-view="'msg-' + messages.length" :scroll-with-animation="true" ref="chatScroll">
			<view v-for="(msg, index) in messages" :key="index" :id="'msg-' + (index + 1)" class="message-item" :class="{ 'robot': msg.from === 'robot', 'user': msg.from === 'user' }">
				<view class="message-avatar">
					<image :src="msg.from === 'customer' || msg.from === 'robot' ? `${apiBaseUrl}/uploads/static/robot-avatar.png` : `${apiBaseUrl}/uploads/static/user-avatar.png`"></image>
				</view>
				<view class="message-content">  
					<!-- 语音消息部分 -->
					<view class="voice-message-container" v-if="msg.voiceUrl">
						<view class="voice-message" :class="{ 'playing': msg.isPlaying }" :style="{ width: calculateVoiceWidth(msg.duration || 3) }" @click="playVoice(msg.voiceUrl, index)">
							<view class="voice-icon" :class="{ 'playing': msg.isPlaying }">
								<span></span>
							</view>
							<view class="voice-duration">{{msg.duration || 3}}''</view>
						</view>
					</view>
					
					<!-- 文字内容部分 -->
					<view class="text-content-container">
						<!-- 文字转录 -->
						<view class="text-transcript">
							<text>{{msg.text}}</text>
						</view>
						
						<!-- 改进建议（仅用户消息显示） -->
						<view v-if="msg.from === 'user' && msg.suggestion" class="suggestion-wrapper">
							<view class="suggestion-btn" @click="toggleSuggestion(index)">
								<text>{{msg.showSuggestion ? '收起表达建议' : '查看表达建议'}}</text>
							</view>
							<view class="suggestion-content" v-if="msg.showSuggestion">
								<view class="suggestion-title">表达建议</view>
								<text class="suggestion-text">{{msg.suggestion}}</text>
							</view>
						</view>
					</view>
				</view>
			</view>
		</scroll-view>
		
		<!-- 底部操作按钮 -->
		<view class="action-buttons">
			<button class="back-btn" @click="goBack">返回</button>
			<button class="report-btn" @click="viewReport">查看报告</button>
		</view>
	</view>
</template>

<script>
	import config from '@/config.js'
	
	export default {
		data() {
			return {
				sceneId: 0,
				sceneName: '',
				practiceId: '',
				practiceDate: '',
				messages: [],
				apiBaseUrl: config.apiBaseUrl,
				currentAudioContext: null,
				currentPlayingIndex: -1
			}
		},
		onLoad(options) {
			if (options.practiceId) {
				this.practiceId = options.practiceId;
				this.sceneId = parseInt(options.sceneId || 0);
				this.loadChatHistory();
				this.getSceneInfo();
			}
		},
		onHide() {
			// 页面隐藏时停止正在播放的音频
			console.log('页面隐藏，停止音频播放');
			this.stopCurrentAudio();
		},
		onUnload() {
			// 页面卸载时停止正在播放的音频
			console.log('页面卸载，停止音频播放');
			this.stopCurrentAudio();
		},
		methods: {
			loadChatHistory() {
				const token = uni.getStorageSync('token');
				const header = {
					'Authorization': `Bearer ${token}`,
					'Content-Type': 'application/json'
				};

				uni.showLoading({ title: '加载对话记录...' });
				
				uni.request({
					url: this.apiBaseUrl + '/api/report/get-chat-history',
					method: 'POST',
					data: { practice_id: this.practiceId },
					header,
					success: (res) => {
						if (res.data && res.data.success) {
							const chatHistory = res.data.data || [];
							this.messages = chatHistory.map(msg => ({
								...msg,
								showSuggestion: false,
								isPlaying: false
							}));
							
							// 设置练习日期
							if (chatHistory.length > 0) {
								const firstMsg = chatHistory[0];
								if (firstMsg.timestamp) {
									this.practiceDate = new Date(firstMsg.timestamp).toLocaleDateString();
								}
							}
						} else {
							uni.showToast({ title: '加载对话记录失败', icon: 'none' });
						}
					},
					fail: (err) => {
						console.error('获取对话记录失败:', err);
						uni.showToast({ title: '加载对话记录失败', icon: 'none' });
					},
					complete: () => {
						uni.hideLoading();
					}
				});
			},
			getSceneInfo() {
				const sceneNames = {
					0: '核苷酸介绍',
					1: '新客户开发',
					2: '异议处理',
					3: '产品推荐',
					4: '成交技巧'
				};
				this.sceneName = sceneNames[this.sceneId] || '未知场景';
			},
			calculateVoiceWidth(duration) {
				// 将时长转换为数字
				const durationNum = parseInt(duration) || 0;
				
				// 根据时长计算宽度，时长越长宽度越大
				// 这里使用一个简单的线性映射，可以根据需要调整
				const minVoiceWidth = 120; // 最小宽度（rpx）
				const maxVoiceWidth = 400; // 最大宽度（rpx）
				
				let width = minVoiceWidth + (durationNum / 60) * (maxVoiceWidth - minVoiceWidth);
				
				// 确保宽度在最小和最大值之间
				width = Math.max(minVoiceWidth, Math.min(width, maxVoiceWidth));
				
				return width + 'rpx';
			},
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
				const msg = this.messages[index];
				msg.showSuggestion = !msg.showSuggestion;
				this.$set(this.messages, index, msg);
			},
			goBack() {
				// 停止正在播放的音频
				this.stopCurrentAudio();
				uni.navigateBack();
			},
			viewReport() {
				uni.navigateTo({
					url: `/pages/report/report?practiceId=${this.practiceId}&conversationId=${this.conversationId}`
				});
			},
			// 停止当前正在播放的音频
			stopCurrentAudio() {
				if (this.currentAudioContext) {
					try {
						this.currentAudioContext.stop();
						this.currentAudioContext.destroy();
						this.currentAudioContext = null;
					} catch (e) {
						console.error('停止音频失败:', e);
					}
				}
				
				// 重置播放状态
				if (this.currentPlayingIndex >= 0 && this.currentPlayingIndex < this.messages.length) {
					this.$set(this.messages[this.currentPlayingIndex], 'isPlaying', false);
				}
				this.currentPlayingIndex = -1;
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
		background-color: #10b981;
		color: #fff;
		padding: 30rpx;
		text-align: center;
	}
	
	.scene-name {
		font-size: 36rpx;
		font-weight: bold;
		margin-bottom: 10rpx;
		display: block;
	}
	
	.practice-date {
		font-size: 24rpx;
		opacity: 0.8;
	}
	
	.chat-messages {
		flex: 1;
		padding: 20rpx;
		overflow-y: auto;
	}
	
	.message-item {
		display: flex;
		align-items: flex-start;
		margin-bottom: 30rpx;
		padding: 15rpx 0;
	}

	.message-item.user {
		flex-direction: row-reverse;
	}

	.message-item.robot {
		flex-direction: row;
	}

	.message-avatar {
		width: 80rpx;
		height: 80rpx;
		border-radius: 40rpx;
		overflow: hidden;
		margin-right: 20rpx;
		flex-shrink: 0;
		box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
	}

	.message-item.user .message-avatar {
		margin-right: 0;
		margin-left: 20rpx;
	}

	.message-avatar image {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.message-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		justify-content: center;
		max-width: 70%;
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
		cursor: pointer;
		box-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.1);
	}

	.voice-message:hover {
		background-color: #e0e0e0;
	}

	.voice-message.playing {
		background-color: #e8f5e8;
		border: 2rpx solid #10b981;
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
	
	.voice-duration {
		font-size: 24rpx;
		color: #666;
		margin-left: 10rpx;
	}

	.user .voice-message {
		flex-direction: row-reverse;
		background-color: #95EC69;
	}

	.user .voice-icon {
		margin-right: 0;
		margin-left: 10rpx;
	}

	.user .voice-duration {
		margin-right: 10rpx;
		color: #666;
	}

	.robot .voice-duration {
		color: #666;
	}
	
	.text-content-container {
		display: flex;
		flex-direction: column;
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
		color: #333;
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
	
	.action-buttons {
		display: flex;
		justify-content: space-between;
		padding: 30rpx;
		background-color: #fff;
		border-top: 1rpx solid #eee;
	}
	
	.back-btn, .report-btn {
		width: 48%;
		height: 80rpx;
		line-height: 80rpx;
		text-align: center;
		border-radius: 40rpx;
		font-size: 30rpx;
	}
	
	.back-btn {
		background-color: #f2f2f2;
		color: #333;
	}
	
	.report-btn {
		background-color: #10b981;
		color: #fff;
	}

	.robot .voice-icon {
		filter: brightness(0) saturate(100%) invert(40%) sepia(82%) saturate(1644%) hue-rotate(199deg) brightness(97%) contrast(101%);
	}

	.robot .voice-icon.playing {
		animation: voice-wave 1.5s ease-in-out infinite;
		transform-origin: center;
	}
</style> 