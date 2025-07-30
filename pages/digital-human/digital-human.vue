<template>
	<view class="digital-human-container">
		<!-- 顶部标题栏 -->
		<view class="header">
			<text class="title">数字人助手</text>
		</view>
		
		<!-- 主要内容区域 -->
		<view class="content">
			<!-- 数字人介绍 -->
			<view class="intro-card">
				<image class="avatar" src="/static/digital-human-avatar.png" mode="aspectFill"></image>
				<view class="intro-text">
					<text class="name">智能数字人</text>
					<text class="description">专业的AI助手，为您提供智能实时对话服务，数字人视频制作服务</text>
				</view>
			</view>
			
			<!-- 语音对话功能说明 -->
			<view class="voice-features">
				<view class="feature-header">
					<uni-icons type="mic" size="24" color="#1AAD19"></uni-icons>
					<text class="feature-title">实时语音对话</text>
				</view>
				<view class="voice-description">
					<!-- <text class="desc-text">• 实时语音识别，支持语音输入，准确率高，响应速度快，提升交互体验</text> -->
                    <text class="desc-text">• 准确率高，响应速度快，提升交互体验</text>
				</view>
                <view class="feature-header">
                	<uni-icons type="mic" size="24" color="#1AAD19"></uni-icons>
                	<text class="feature-title">数字人制作</text>
                </view>
                <view class="voice-description">
                    <text class="desc-text">•点击制作数字人完成数字人克隆，音色克隆后合成数字人，合成视频列表展示合成的数字人视频</text>
                	<!-- <text class="desc-text">• 支持“直传”与“分步式（克隆+合成）”两套流程制作数字人，支持克隆语音语色合成数字人</text> -->
                </view>
			</view>
			
			<!-- 功能按钮 -->
			<view class="button-container">
<!-- 				<button class="primary-btn" @click="openDigitalHuman">
					<uni-icons type="chat" size="20" color="#fff"></uni-icons>
					<text class="btn-text">实时语音对话（VIP专享）</text>
				</button>
				<button class="create-btn" @click="createDigitalHuman">
					<uni-icons type="plus" size="20" color="#fff"></uni-icons>
					<text class="btn-text">制作数字人（直传）</text>
				</button> -->
				<button class="clone-btn" @click="goToCloneDigitalHuman">
					<uni-icons type="person" size="20" color="#fff"></uni-icons>
					<text class="btn-text">制作数字人</text>
				</button>
				<button class="video-list-btn" @click="goToSynthesizeList">
					<uni-icons type="videocam" size="20" color="#fff"></uni-icons>
					<text class="btn-text">合成视频列表</text>
				</button>
			</view>
			</view>
		</view>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				
			};
		},
		methods: {
			openDigitalHuman() {
				// 跳转到外部数字人页面
				uni.navigateTo({
					url: '/pages/digital_webview/digital_webview'
				});
			},
			openVoiceChat() {
				// 跳转到语音对话页面
				uni.navigateTo({
					url: '/pages/voice-chat/voice-chat'
				});
			},
			createDigitalHuman() {
				// 跳转到制作数字人页面
				uni.navigateTo({
					url: '/pages/create-digital-human/create-digital-human'
				});
			},
			goToCloneDigitalHuman() {
				uni.navigateTo({
					url: '/pages/create-digital-human-advanced/create-digital-human-advanced'
				});
			},
			goToSynthesizeList() {
                console.log(uni.getStorageSync('token'))
				uni.navigateTo({
					url: '/pages/synthesize-list/synthesize-list'
				});
			}
		}
	}
</script>

<style>
	.digital-human-container {
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		padding: 0;
	}
	
	.header {
		background: rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(10px);
		padding: 40rpx 30rpx 20rpx;
		text-align: center;
	}
	
	.title {
		font-size: 36rpx;
		font-weight: bold;
		color: #fff;
	}
	
	.content {
		padding: 40rpx 30rpx;
	}
	
	.intro-card {
		background: rgba(255, 255, 255, 0.95);
		border-radius: 20rpx;
		padding: 40rpx;
		margin-bottom: 40rpx;
		display: flex;
		align-items: center;
		box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.1);
	}
	
	.avatar {
		width: 120rpx;
		height: 120rpx;
		border-radius: 60rpx;
		margin-right: 30rpx;
		background: #f0f0f0;
	}
	
	.intro-text {
		flex: 1;
	}
	
	.name {
		font-size: 32rpx;
		font-weight: bold;
		color: #333;
		display: block;
		margin-bottom: 8rpx;
	}
	
	.description {
		font-size: 26rpx;
		color: #666;
		line-height: 1.5;
	}
	
	.button-container {
		margin-bottom: 40rpx;
		display: flex;
		flex-direction: column;
		gap: 20rpx;
		align-items: center;
	}
	.primary-btn,
	.create-btn,
	.clone-btn,
	.video-list-btn {
		width: 80%;
		max-width: 600rpx;
		min-width: 300rpx;
		justify-content: center;
	}
	
	.primary-btn {
		background: linear-gradient(45deg, #1AAD19, #07C160);
		border: none;
		border-radius: 50rpx;
		padding: 30rpx 60rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 8rpx 24rpx rgba(26, 173, 25, 0.3);
		transition: all 0.3s ease;
	}
	
	.primary-btn:active {
		transform: translateY(2rpx);
		box-shadow: 0 4rpx 12rpx rgba(26, 173, 25, 0.3);
	}
	
	.create-btn {
		background: linear-gradient(45deg, #667eea, #764ba2);
		border: none;
		border-radius: 50rpx;
		padding: 30rpx 60rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 8rpx 24rpx rgba(102, 126, 234, 0.3);
		transition: all 0.3s ease;
	}
	
	.create-btn:active {
		transform: translateY(2rpx);
		box-shadow: 0 4rpx 12rpx rgba(102, 126, 234, 0.3);
	}
	
	.voice-btn {
		background: linear-gradient(45deg, #FF6B6B, #FF8E53);
		border: none;
		border-radius: 50rpx;
		padding: 30rpx 60rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 8rpx 24rpx rgba(255, 107, 107, 0.3);
		transition: all 0.3s ease;
	}
	
	.voice-btn:active {
		transform: translateY(2rpx);
		box-shadow: 0 4rpx 12rpx rgba(255, 107, 107, 0.3);
	}
	
	.btn-text {
		color: #fff;
		font-size: 30rpx;
		font-weight: bold;
		margin-left: 10rpx;
	}
	
	.voice-features {
		background: rgba(255, 255, 255, 0.9);
		border-radius: 20rpx;
		padding: 30rpx;
		margin-bottom: 40rpx;
	}
	
	.feature-header {
		display: flex;
		align-items: center;
		margin-bottom: 20rpx;
	}
	
	.feature-title {
		font-size: 28rpx;
		color: #333;
		margin-left: 15rpx;
	}
	
	.voice-description {
		font-size: 26rpx;
		color: #666;
		line-height: 1.5;
	}
	
	.desc-text {
		display: block;
		margin-bottom: 10rpx;
	}
	
	.features {
		background: rgba(255, 255, 255, 0.9);
		border-radius: 20rpx;
		padding: 30rpx;
	}
	
	.feature-item {
		display: flex;
		align-items: center;
		margin-bottom: 20rpx;
	}
	
	.feature-item:last-child {
		margin-bottom: 0;
	}
	
	.feature-text {
		font-size: 28rpx;
		color: #333;
		margin-left: 15rpx;
	}
	.clone-btn {
		background: linear-gradient(45deg, #ff9800, #ff5722);
		border: none;
		border-radius: 50rpx;
		padding: 30rpx 60rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 8rpx 24rpx rgba(255, 152, 0, 0.3);
		transition: all 0.3s ease;
		margin-top: 20rpx;
	}
	.video-list-btn {
		background: linear-gradient(45deg, #00bcd4, #2196f3);
		border: none;
		border-radius: 50rpx;
		padding: 30rpx 60rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 8rpx 24rpx rgba(33, 150, 243, 0.3);
		transition: all 0.3s ease;
		margin-top: 20rpx;
	}
	.video-list-btn:active {
		transform: translateY(2rpx);
		box-shadow: 0 4rpx 12rpx rgba(33, 150, 243, 0.3);
	}
</style> 