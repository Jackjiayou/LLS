<template>
	<view class="user-info-container">
		<view class="header">
			<text class="title">用户信息</text>
		</view>
		
		<view class="info-card">
			<view class="info-item">
				<text class="label">用户ID:</text>
				<text class="value">{{userInfo.id}}</text>
			</view>
			<view class="info-item">
				<text class="label">OpenID:</text>
				<text class="value openid">{{userInfo.openid}}</text>
				<button @click="copyOpenid" class="copy-btn">复制</button>
			</view>
			<view class="info-item">
				<text class="label">昵称:</text>
				<text class="value">{{userInfo.nickname || '未设置'}}</text>
			</view>
			<view class="info-item">
				<text class="label">注册时间:</text>
				<text class="value">{{formatDate(userInfo.created_at)}}</text>
			</view>
		</view>
		
		<view class="tips">
			<text class="tips-title">💡 提示</text>
			<text class="tips-content">复制上面的OpenID，然后到白名单管理页面添加用户</text>
		</view>
		
		<view class="actions">
			<button @click="goToWhitelist" class="action-btn">去白名单管理</button>
		</view>
	</view>
</template>

<script>
	import config from '@/config.js'
	
	export default {
		data() {
			return {
				apiBaseUrl: config.apiBaseUrl,
				userInfo: {
					id: '',
					openid: '',
					nickname: '',
					avatar_url: '',
					created_at: ''
				}
			}
		},
		onLoad() {
			this.loadUserInfo()
		},
		methods: {
			// 加载用户信息
			async loadUserInfo() {
				try {
					const token = uni.getStorageSync('token')
					const res = await uni.request({
						url: `${this.apiBaseUrl}/auth/user-info`,
						method: 'GET',
						header: {
							'Authorization': `Bearer ${token}`
						}
					})
					
					if (res.statusCode === 200) {
						this.userInfo = res.data
					} else {
						uni.showToast({
							title: '获取用户信息失败',
							icon: 'none'
						})
					}
				} catch (error) {
					console.error('Load user info error:', error)
					uni.showToast({
						title: '网络错误',
						icon: 'none'
					})
				}
			},
			
			// 复制openid
			copyOpenid() {
				uni.setClipboardData({
					data: this.userInfo.openid,
					success: () => {
						uni.showToast({
							title: 'OpenID已复制',
							icon: 'success'
						})
					}
				})
			},
			
			// 跳转到白名单管理
			goToWhitelist() {
				uni.navigateTo({
					url: '/pages/admin/whitelist'
				})
			},
			
			// 格式化日期
			formatDate(dateString) {
				if (!dateString) return '未知'
				const date = new Date(dateString)
				return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
			}
		}
	}
</script>

<style>
	.user-info-container {
		min-height: 100vh;
		background: #f7f7f7;
		padding: 20rpx;
	}
	
	.header {
		background: #fff;
		padding: 30rpx;
		border-radius: 16rpx;
		margin-bottom: 20rpx;
		text-align: center;
	}
	
	.title {
		font-size: 32rpx;
		font-weight: bold;
		color: #333;
	}
	
	.info-card {
		background: #fff;
		padding: 30rpx;
		border-radius: 16rpx;
		margin-bottom: 20rpx;
	}
	
	.info-item {
		display: flex;
		align-items: center;
		padding: 20rpx 0;
		border-bottom: 1rpx solid #f0f0f0;
	}
	
	.info-item:last-child {
		border-bottom: none;
	}
	
	.label {
		width: 160rpx;
		font-size: 28rpx;
		color: #666;
	}
	
	.value {
		flex: 1;
		font-size: 28rpx;
		color: #333;
	}
	
	.openid {
		font-family: monospace;
		background: #f5f5f5;
		padding: 8rpx 12rpx;
		border-radius: 6rpx;
		margin-right: 20rpx;
	}
	
	.copy-btn {
		background: #1AAD19;
		color: #fff;
		padding: 8rpx 16rpx;
		border-radius: 6rpx;
		font-size: 24rpx;
	}
	
	.tips {
		background: #e8f5e8;
		padding: 30rpx;
		border-radius: 16rpx;
		margin-bottom: 20rpx;
	}
	
	.tips-title {
		font-size: 28rpx;
		font-weight: bold;
		color: #1AAD19;
		display: block;
		margin-bottom: 10rpx;
	}
	
	.tips-content {
		font-size: 26rpx;
		color: #666;
		line-height: 1.5;
	}
	
	.actions {
		padding: 20rpx 0;
	}
	
	.action-btn {
		background: #1AAD19;
		color: #fff;
		padding: 24rpx;
		border-radius: 12rpx;
		font-size: 30rpx;
		width: 100%;
	}
</style> 