<template>
	<view class="agent-container">
		<!-- 网页版链接 -->
<!-- 		<view class="web-version-card">
			<text class="web-version-text">网页版: trytalks.com</text>
			<button class="copy-btn" @click="copyLink">复制</button>
		</view> -->

		<!-- 工具列表 -->
		<view class="tool-list">
			<view v-for="tool in tools" :key="tool.id" class="tool-item" @click="goToTool(tool)">
				<image class="tool-icon" :src="tool.icon"></image>
				<view class="tool-info">
					<text class="tool-title">{{ tool.title }}</text>
					<text class="tool-desc">{{ tool.description }}</text>
				</view>
			</view>
		</view>
		
		<!-- 更多工具提示 -->
		<view class="more-tools-tip">
			<view class="divider"></view>
			<text class="tip-text">更多AI工具敬请期待!</text>
			<view class="divider"></view>
		</view>
	</view>
</template>

<script>
	import config from '@/config.js'
	
	export default {
		data() {
			return {
				apiBaseUrl: config.apiBaseUrl,
				tools: [
					{
						id: 1,
						title: '智问助手',
						description: '为你解答接待顾客过程中遇到的问题。',
						icon: `${config.apiBaseUrl}/uploads/static/assistant.png`,
						url: '/pages/assistant/assistant',
                        h5Url: 'https://dify.dizhijia.cn/chat/i5qWaOxq1ESuQJ9v'
					},
					{
						id: 2,
						title: '写个邀约短信',
						description: '生日、售后、节日、活动等邀约信息撰写。',
						icon: `${config.apiBaseUrl}/uploads/static/birthday.png`,
						url: '',
                        h5Url: 'https://dify.dizhijia.cn/workflow/T6INFmZIORXD0X0a'
					},
					{
						id: 3,
						title: '小红书爆款生成器',
						description: '一键生成爆款文案，带你勇闯自媒体，你的文章在人海中脱颖而出。',
						icon: `${config.apiBaseUrl}/uploads/static/red.png`,
						url: ''
					},
					{
						id: 4,
						title: '发朋友圈营销文案',
						description: '帮你打造高转化率的朋友圈营销文案，你的每一条朋友圈都变成销售利器。',
						icon: `${config.apiBaseUrl}/uploads/static/friend.png`,
						url: ''
					},
					{
						id: 5,
						title: '为产品写小红书营销文案',
						description: '轻松撰写出吸引人的小红书营销文案。',
						icon: `${config.apiBaseUrl}/uploads/static/redbook.png`,
						url: ''
					}
				]
			};
		},
		methods: {
			copyLink() {
				uni.setClipboardData({
					data: 'trytalks.com',
					success: () => {
						uni.showToast({
							title: '复制成功',
							icon: 'none'
						});
					}
				});
			},
			goToTool(tool) {
			  if (tool.h5Url) {
			    uni.navigateTo({
			      url: `/pages/webview/webview?url=${encodeURIComponent(tool.h5Url)}`
			    });
			  } else {
			    uni.showToast({
			      title: '功能开发中，敬请期待',
			      icon: 'none'
			    });
			  }
			}
		}
	}
</script>

<style>
	.agent-container {
		background-color: #f7f8fa;
		min-height: 100vh;
		padding: 24rpx;
	}

	.web-version-card {
		display: flex;
		align-items: center;
		justify-content: space-between;
		background-color: #ffffff;
		border-radius: 16rpx;
		padding: 24rpx;
		margin-bottom: 24rpx;
		box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
	}

	.web-version-text {
		font-size: 28rpx;
		color: #333;
	}

	.copy-btn {
		font-size: 24rpx;
		background-color: #10b981;
		color: #fff;
		padding: 8rpx 24rpx;
		border-radius: 30rpx;
		line-height: 1.5;
		margin: 0;
	}
	
	.tool-list {
		background-color: #ffffff;
		border-radius: 16rpx;
		padding: 0 24rpx;
		box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
	}

	.tool-item {
		display: flex;
		align-items: center;
		padding: 32rpx 0;
		border-bottom: 1rpx solid #f0f0f0;
	}
	
	.tool-item:last-child {
		border-bottom: none;
	}

	.tool-icon {
		width: 100rpx;
		height: 100rpx;
		border-radius: 50%;
		margin-right: 24rpx;
		flex-shrink: 0;
	}

	.tool-info {
		display: flex;
		flex-direction: column;
		gap: 8rpx;
	}

	.tool-title {
		font-size: 30rpx;
		font-weight: bold;
		color: #333;
	}

	.tool-desc {
		font-size: 24rpx;
		color: #888;
	}
	
	.more-tools-tip {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 40rpx 0;
		margin-top: 20rpx;
	}
	
	.divider {
		flex: 1;
		height: 1rpx;
		background-color: #e0e0e0;
	}
	
	.tip-text {
		color: #aaa;
		font-size: 24rpx;
		margin: 0 24rpx;
	}
</style> 