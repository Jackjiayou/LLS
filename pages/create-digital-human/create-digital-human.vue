<template>
	<view class="create-digital-human-container">
		<!-- 顶部标题栏 -->
		<view class="header">
			<view class="header-left" @click="goBack">
				<uni-icons type="left" size="24" color="#fff"></uni-icons>
			</view>
			<text class="title">制作数字人</text>
			<view class="header-right"></view>
		</view>
		
		<!-- 主要内容区域 -->
		<view class="content">
			<!-- 说明文字 -->
			<view class="intro-section">
				<text class="intro-title">上传素材制作专属数字人</text>
				<text class="intro-desc">请上传以下素材，我们将为您生成个性化的数字人</text>
			</view>
			
			<!-- 上传功能区域 -->
			<view class="upload-section">
				
				<!-- 上传视频 -->
				<view class="upload-item" @click="uploadVideo">
					<view class="upload-icon">
						<uni-icons type="videocam" size="32" color="#FF6B6B"></uni-icons>
					</view>
					<view class="upload-content">
						<text class="upload-title">上传视频</text>
						<text class="upload-desc">上传人物视频，用于学习动作和表情</text>
						<text class="upload-status" v-if="videoFile">{{ videoFile.name }}</text>
					</view>
					<view class="upload-arrow">
						<uni-icons type="right" size="16" color="#999"></uni-icons>
					</view>
				</view>
				
				
				<!-- 上传音频 -->
				<view class="upload-item" @click="uploadAudio">
					<view class="upload-icon">
						<uni-icons type="sound" size="32" color="#FF8E53"></uni-icons>
					</view>
					<view class="upload-content">
						<text class="upload-title">上传音频</text>
						<text class="upload-desc">上传语音样本，用于学习说话风格</text>
						<text class="upload-status" v-if="audioFile">{{ audioFile.name }}</text>
					</view>
					<view class="upload-arrow">
						<uni-icons type="right" size="16" color="#999"></uni-icons>
					</view>
				</view>
			</view>
			
			<!-- 开始制作按钮 -->
			<view class="action-section">
				<button class="create-btn" @click="startCreation" :disabled="!canCreate">
					<uni-icons type="gear" size="20" color="#fff"></uni-icons>
					<text class="btn-text">开始制作数字人</text>
				</button>
			</view>
		</view>
				
		<view v-if="isRecording" class="recording-indicator">
			<view class="recording-dot"></view>
			<text class="recording-text">录音中... {{ recordDuration }}s</text>
			<button class="stop-record-btn" @click="stopRecording" size="mini" type="warn">停止录音</button>
		</view>
		
		<view v-if="generateVideoPath" class="generate-video-section">
			<text class="generate-video-title">生成视频已就绪</text>
			<!-- 视频预览 -->
			<video
				v-if="generateVideoPath"
				:src="generateVideoPath"
				controls
				style="width: 100%; max-width: 600rpx; margin: 20rpx auto; display: block; border-radius: 16rpx;"
			></video>
			<view class="generate-video-path">{{ generateVideoPath }}</view>
			<!-- H5下载 -->
			<button v-if="isH5" @click="downloadVideoH5" class="download-btn">下载视频</button>
			<!-- 小程序保存 -->
			<button v-else @click="downloadVideoMp" class="download-btn">保存到本地</button>
		</view>
	</view>
</template>

<script>
	import config from '@/config.js'
	export default {
		data() {
			return {
				videoFile: null,
				audioFile: null,
				isCreating: false,
				isRecording: false,
				recordDuration: 0,
				recordTimer: null,
				generateVideoPath: ''
			};
		},
		computed: {
			canCreate() {
				return this.imageFile || this.videoFile || this.textContent || this.audioFile;
			},
			isH5() {
				// #ifdef H5
				return true;
				// #endif
				// #ifndef H5
				return false;
				// #endif
			}
		},
		methods: {
			goBack() {
				uni.navigateBack();
			},
			
			// 上传图片
			uploadImage() {
				uni.chooseImage({
					count: 1,
					sizeType: ['original', 'compressed'],
					sourceType: ['album', 'camera'],
					success: (res) => {
						const tempFilePath = res.tempFilePaths[0];
						this.uploadFile('image', tempFilePath);
					}
				});
			},
			
			// 上传视频
			uploadVideo() {
				uni.chooseVideo({
					sourceType: ['album', 'camera'],
					maxDuration: 60,
					camera: 'back',
					success: (res) => {
						const tempFilePath = res.tempFilePath;
						this.uploadFile('video', tempFilePath);
					}
				});
			},
			
			// 上传音频
			uploadAudio() {
				// #ifdef H5 || APP-PLUS
				uni.chooseFile({
					count: 1,
					type: 'file',
					extension: ['.mp3', '.wav', '.m4a'],
					success: (res) => {
						const tempFilePath = res.tempFiles[0].path;
						this.uploadFile('audio', tempFilePath);
					}
				});
				// #endif
				// #ifdef MP-WEIXIN
				const recorderManager = uni.getRecorderManager();
				uni.showModal({
					title: '录音上传',
					content: '请录制一段音频作为语音样本，录音结束后点击"停止录音"按钮',
					success: (res) => {
						if (res.confirm) {
							this.isRecording = true;
							this.recordDuration = 0;
							this.recordTimer = setInterval(() => {
								this.recordDuration++;
							}, 1000);
							recorderManager.start({
								format: 'mp3',
								duration: 60000 // 最长60秒
							});
						}
					}
				});
				recorderManager.onStop((res) => {
					this.isRecording = false;
					clearInterval(this.recordTimer);
					this.uploadFile('audio', res.tempFilePath);
				});
				// #endif
			},
			
			// 上传文字
			uploadText() {
				this.$refs.textPopup.open();
			},
			
			// 关闭文字弹窗
			closeTextPopup() {
				this.$refs.textPopup.close();
			},
			
			// 确认文字输入
			confirmText() {
				if (this.textContent.trim()) {
					this.closeTextPopup();
					uni.showToast({
						title: '文字内容已保存',
						icon: 'success'
					});
				} else {
					uni.showToast({
						title: '请输入文字内容',
						icon: 'none'
					});
				}
			},
			
			// 上传文件到服务器
			uploadFile(type, filePath) {
				uni.showLoading({
					title: '上传中...'
				});
				
				uni.uploadFile({
					url: config.apiBaseUrl+ `/api/digital-human/upload-${type}`,
					filePath: filePath,
					name: 'file',
					header: {
						'Authorization': `Bearer ${uni.getStorageSync('token')}`
					},
					success: (res) => {
						uni.hideLoading();
						const data = JSON.parse(res.data);
						if (data.success) {
							// 保存文件信息
							const fileInfo = {
								name: filePath.split('/').pop(),
								url: data.file_url,
								id: data.file_id
							};
							
							switch (type) {
								case 'image':
									this.imageFile = fileInfo;
									break;
								case 'video':
									this.videoFile = fileInfo;
									break;
								case 'audio':
									this.audioFile = fileInfo;
									break;
							}
							
							uni.showToast({
								title: '上传成功',
								icon: 'success'
							});
						} else {
							uni.showToast({
								title: data.message || '上传失败',
								icon: 'none'
							});
						}
					},
					fail: (err) => {
						uni.hideLoading();
						uni.showToast({
							title: '上传失败',
							icon: 'none'
						});
						console.error('上传失败:', err);
					}
				});
			},
			
			// 开始制作数字人
			startCreation() {
				if (this.isCreating) return;
				
				this.isCreating = true;
				uni.showLoading({
					title: '制作中...'
				});
				
				// 准备提交数据
				const submitData = {
					video_id: this.videoFile?.id,
					audio_id: this.audioFile?.id
				};
				
				uni.request({
					url: config.apiBaseUrl + '/api/digital-human/create',
					method: 'POST',
					header: {
						'Authorization': `Bearer ${uni.getStorageSync('token')}`,
						'Content-Type': 'application/json'
					},
                    timeout:180000,
					data: submitData,
					success: (res) => {
						uni.hideLoading();
						this.isCreating = false;
						
						if (res.data.success) {
							this.generateVideoPath = res.data.generate_video_path;
							uni.showToast({
								title: '制作成功',
								icon: 'success'
							});
						} else {
							uni.showToast({
								title: res.data.message || '制作失败',
								icon: 'none'
							});
						}
					},
					fail: (err) => {
						uni.hideLoading();
						this.isCreating = false;
						uni.showToast({
							title: '制作失败',
							icon: 'none'
						});
						console.error('制作失败:', err);
					}
				});
			},
			stopRecording() {
				// #ifdef MP-WEIXIN
				const recorderManager = uni.getRecorderManager();
				recorderManager.stop();
				// #endif
			},
			downloadVideoH5() {
				// 直接用a标签下载
				const link = document.createElement('a');
				link.href = this.generateVideoPath;
				link.download = '数字人视频.mp4';
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
			},
			downloadVideoMp() {
				// 微信小程序端
				uni.downloadFile({
					url: this.generateVideoPath,
					success: (res) => {
						if (res.statusCode === 200) {
							// 保存到相册
							uni.saveVideoToPhotosAlbum({
								filePath: res.tempFilePath,
								success: () => {
									uni.showToast({ title: '已保存到相册', icon: 'success' });
								},
								fail: () => {
									uni.showToast({ title: '保存失败', icon: 'none' });
								}
							});
						} else {
							uni.showToast({ title: '下载失败', icon: 'none' });
						}
					},
					fail: () => {
						uni.showToast({ title: '下载失败', icon: 'none' });
					}
				});
			}
		}
	}
</script>

<style>
	.create-digital-human-container {
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		padding: 0;
	}
	
	.header {
		background: rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(10px);
		padding: 40rpx 30rpx 20rpx;
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	
	.header-left {
		width: 60rpx;
		height: 60rpx;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.title {
		font-size: 36rpx;
		font-weight: bold;
		color: #fff;
	}
	
	.header-right {
		width: 60rpx;
	}
	
	.content {
		padding: 40rpx 30rpx;
	}
	
	.intro-section {
		background: rgba(255, 255, 255, 0.95);
		border-radius: 20rpx;
		padding: 40rpx;
		margin-bottom: 40rpx;
		text-align: center;
		box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.1);
	}
	
	.intro-title {
		font-size: 32rpx;
		font-weight: bold;
		color: #333;
		display: block;
		margin-bottom: 16rpx;
	}
	
	.intro-desc {
		font-size: 26rpx;
		color: #666;
		line-height: 1.5;
	}
	
	.upload-section {
		margin-bottom: 40rpx;
	}
	
	.upload-item {
		background: rgba(255, 255, 255, 0.95);
		border-radius: 20rpx;
		padding: 30rpx;
		margin-bottom: 20rpx;
		display: flex;
		align-items: center;
		box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
		transition: all 0.3s ease;
	}
	
	.upload-item:active {
		transform: scale(0.98);
	}
	
	.upload-icon {
		width: 80rpx;
		height: 80rpx;
		background: rgba(26, 173, 25, 0.1);
		border-radius: 40rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-right: 30rpx;
	}
	
	.upload-content {
		flex: 1;
	}
	
	.upload-title {
		font-size: 30rpx;
		font-weight: bold;
		color: #333;
		display: block;
		margin-bottom: 8rpx;
	}
	
	.upload-desc {
		font-size: 24rpx;
		color: #666;
		display: block;
		margin-bottom: 8rpx;
	}
	
	.upload-status {
		font-size: 22rpx;
		color: #1AAD19;
		display: block;
	}
	
	.upload-arrow {
		width: 40rpx;
		height: 40rpx;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.action-section {
		margin-top: 40rpx;
	}
	
	.create-btn {
		background: linear-gradient(45deg, #1AAD19, #07C160);
		border: none;
		border-radius: 50rpx;
		padding: 30rpx 60rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 8rpx 24rpx rgba(26, 173, 25, 0.3);
		transition: all 0.3s ease;
		width: 100%;
	}
	
	.create-btn:active {
		transform: translateY(2rpx);
		box-shadow: 0 4rpx 12rpx rgba(26, 173, 25, 0.3);
	}
	
	.create-btn[disabled] {
		background: #ccc;
		box-shadow: none;
	}
	
	.btn-text {
		color: #fff;
		font-size: 30rpx;
		font-weight: bold;
		margin-left: 10rpx;
	}
	
	/* 弹窗样式 */
	.text-popup {
		background: #fff;
		border-radius: 20rpx;
		width: 600rpx;
		max-height: 80vh;
		overflow: hidden;
	}
	
	.popup-header {
		padding: 30rpx;
		border-bottom: 1rpx solid #eee;
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	
	.popup-title {
		font-size: 32rpx;
		font-weight: bold;
		color: #333;
	}
	
	.popup-close {
		width: 40rpx;
		height: 40rpx;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.popup-content {
		padding: 30rpx;
	}
	
	.text-input {
		width: 100%;
		height: 200rpx;
		border: 1rpx solid #ddd;
		border-radius: 10rpx;
		padding: 20rpx;
		font-size: 28rpx;
		line-height: 1.5;
		box-sizing: border-box;
	}
	
	.char-count {
		font-size: 24rpx;
		color: #999;
		text-align: right;
		margin-top: 10rpx;
		display: block;
	}
	
	.popup-actions {
		padding: 30rpx;
		display: flex;
		gap: 20rpx;
		border-top: 1rpx solid #eee;
	}
	
	.popup-btn {
		flex: 1;
		height: 80rpx;
		border-radius: 40rpx;
		font-size: 28rpx;
		border: none;
	}
	
	.cancel-btn {
		background: #f5f5f5;
		color: #666;
	}
	
	.confirm-btn {
		background: linear-gradient(45deg, #1AAD19, #07C160);
		color: #fff;
	}
	
	.recording-indicator {
		position: fixed;
		top: 30%;
		left: 50%;
		transform: translate(-50%, -50%);
		z-index: 9999;
		background: rgba(0,0,0,0.7);
		border-radius: 20rpx;
		padding: 30rpx 40rpx;
		display: flex;
		flex-direction: row;
		align-items: center;
		min-width: 400rpx;
	}
	
	.recording-dot {
		width: 32rpx;
		height: 32rpx;
		border-radius: 50%;
		background: #ff3b30;
		margin-right: 20rpx;
		animation: blink 1s infinite;
		flex-shrink: 0;
	}
	
	@keyframes blink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}
	
	.recording-text {
		color: #fff;
		font-size: 32rpx;
		font-weight: bold;
		flex: 1;
		white-space: nowrap;
	}
	
	.stop-record-btn {
		margin-left: 20rpx;
		height: 48rpx;
		line-height: 48rpx;
		padding: 0 24rpx;
		font-size: 26rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}
	
	.generate-video-section {
		margin: 40rpx 0;
		padding: 30rpx;
		background: #f7f7fa;
		border-radius: 20rpx;
		text-align: center;
	}
	
	.generate-video-title {
		font-size: 32rpx;
		font-weight: bold;
		color: #333;
		margin-bottom: 20rpx;
		display: block;
	}
	
	.generate-video-path {
		font-size: 24rpx;
		color: #666;
		margin-bottom: 20rpx;
		word-break: break-all;
	}
	
	.download-btn {
		background: linear-gradient(45deg, #1AAD19, #07C160);
		color: #fff;
		border-radius: 40rpx;
		font-size: 28rpx;
		padding: 20rpx 40rpx;
	}
</style> 