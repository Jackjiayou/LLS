<template>
	<view class="simple-whitelist-container">
		<view class="header">
			<text class="title">简单白名单管理</text>
		</view>
		
		<view class="add-section">
			<view class="input-group">
				<input 
					v-model="newOpenid" 
					placeholder="请输入用户openid" 
					class="input-field"
				/>
				<input 
					v-model="newNickname" 
					placeholder="用户昵称（可选）" 
					class="input-field"
				/>
				<button @click="addToWhitelist" class="add-btn">添加到白名单</button>
			</view>
		</view>
		
		<view class="tips">
			<text class="tips-title">💡 使用说明</text>
			<text class="tips-content">1. 让用户尝试登录小程序</text>
			<text class="tips-content">2. 用户会收到包含openid的错误信息</text>
			<text class="tips-content">3. 复制openid到上面的输入框</text>
			<text class="tips-content">4. 点击"添加到白名单"</text>
			<text class="tips-content">5. 用户就可以正常登录了</text>
		</view>
		
		<view class="whitelist-section">
			<view class="section-title">当前白名单用户</view>
			<view v-for="user in whitelist" :key="user.id" class="user-item">
				<text class="user-openid">{{user.openid}}</text>
				<text class="user-nickname">{{user.nickname || '未设置昵称'}}</text>
				<button @click="removeFromWhitelist(user.openid)" class="remove-btn">移除</button>
			</view>
			<view v-if="whitelist.length === 0" class="empty-text">暂无白名单用户</view>
		</view>
	</view>
</template>

<script>
	import config from '@/config.js'
	
	export default {
		data() {
			return {
				apiBaseUrl: config.apiBaseUrl,
				newOpenid: '',
				newNickname: '',
				whitelist: []
			}
		},
		onLoad() {
			this.loadWhitelist()
		},
		methods: {
			// 加载白名单
			async loadWhitelist() {
				try {
					const res = await uni.request({
						url: `${this.apiBaseUrl}/api/whitelist/list`,
						method: 'GET'
					})
					
					if (res.statusCode === 200) {
						this.whitelist = res.data.items || []
					}
				} catch (error) {
					console.error('Load whitelist error:', error)
				}
			},
			
			// 添加到白名单
			async addToWhitelist() {
				if (!this.newOpenid.trim()) {
					uni.showToast({
						title: '请输入openid',
						icon: 'none'
					})
					return
				}
				
				try {
					const res = await uni.request({
						url: `${this.apiBaseUrl}/api/whitelist/add?openid=${encodeURIComponent(this.newOpenid.trim())}&nickname=${encodeURIComponent(this.newNickname.trim() || '')}`,
						method: 'POST',
						header: {
							'Content-Type': 'application/json'
						}
					})
					
					if (res.statusCode === 200) {
						uni.showToast({
							title: '添加成功',
							icon: 'success'
						})
						this.newOpenid = ''
						this.newNickname = ''
						this.loadWhitelist()
					} else {
						uni.showToast({
							title: typeof res.data.detail === 'string' ? res.data.detail : '添加失败',
							icon: 'none'
						})
					}
				} catch (error) {
					console.error('Add to whitelist error:', error)
					uni.showToast({
						title: '网络错误',
						icon: 'none'
					})
				}
			},
			
			// 从白名单移除
			async removeFromWhitelist(openid) {
				uni.showModal({
					title: '确认移除',
					content: '确定要将此用户从白名单中移除吗？',
					success: async (res) => {
						if (res.confirm) {
							try {
								const response = await uni.request({
									url: `${this.apiBaseUrl}/api/whitelist/remove/${openid}`,
									method: 'DELETE'
								})
								
								if (response.statusCode === 200) {
									uni.showToast({
										title: '移除成功',
										icon: 'success'
									})
									this.loadWhitelist()
								} else {
									uni.showToast({
										title: typeof response.data.detail === 'string' ? response.data.detail : '移除失败',
										icon: 'none'
									})
								}
							} catch (error) {
								console.error('Remove from whitelist error:', error)
								uni.showToast({
									title: '网络错误',
									icon: 'none'
								})
							}
						}
					}
				})
			}
		}
	}
</script>

<style>
	.simple-whitelist-container {
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
	
	.add-section {
		background: #fff;
		padding: 30rpx;
		border-radius: 16rpx;
		margin-bottom: 20rpx;
	}
	
	.input-group {
		display: flex;
		flex-direction: column;
		gap: 20rpx;
	}
	
	.input-field {
		padding: 20rpx;
		border: 1rpx solid #e0e0e0;
		border-radius: 8rpx;
		font-size: 28rpx;
	}
	
	.add-btn {
		background: #1AAD19;
		color: #fff;
		padding: 20rpx;
		border-radius: 8rpx;
		font-size: 28rpx;
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
		margin-bottom: 15rpx;
	}
	
	.tips-content {
		font-size: 26rpx;
		color: #666;
		line-height: 1.6;
		display: block;
		margin-bottom: 8rpx;
	}
	
	.whitelist-section {
		background: #fff;
		padding: 30rpx;
		border-radius: 16rpx;
	}
	
	.section-title {
		font-size: 30rpx;
		font-weight: bold;
		color: #333;
		margin-bottom: 20rpx;
	}
	
	.user-item {
		display: flex;
		align-items: center;
		padding: 20rpx 0;
		border-bottom: 1rpx solid #f0f0f0;
	}
	
	.user-item:last-child {
		border-bottom: none;
	}
	
	.user-openid {
		flex: 1;
		font-size: 24rpx;
		color: #666;
		font-family: monospace;
	}
	
	.user-nickname {
		flex: 1;
		font-size: 26rpx;
		color: #333;
	}
	
	.remove-btn {
		background: #ff4757;
		color: #fff;
		padding: 8rpx 16rpx;
		border-radius: 6rpx;
		font-size: 24rpx;
	}
	
	.empty-text {
		text-align: center;
		color: #999;
		font-size: 26rpx;
		padding: 40rpx 0;
	}
</style> 