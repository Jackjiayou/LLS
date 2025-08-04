<template>
	<view class="whitelist-container">
		<!-- 顶部标题 -->
		<view class="header">
			<text class="title">白名单管理</text>
		</view>
		
		<!-- 授权码区域 -->
		<view class="auth-codes-section">
			<view class="auth-codes-card">
				<text class="auth-codes-title">授权码列表</text>
				<text class="auth-codes-desc">用户输入以下任一授权码即可自动通过申请</text>
				<view class="auth-codes-list">
					<text v-for="code in authCodes" :key="code" class="auth-code-item">{{code}}</text>
				</view>
			</view>
		</view>
		
		<!-- 添加用户区域 -->
		<view class="add-section">
			<view class="input-group">
				<input 
					v-model="newUser.openid" 
					placeholder="请输入用户openid" 
					class="input-field"
				/>
				<input 
					v-model="newUser.nickname" 
					placeholder="用户昵称（可选）" 
					class="input-field"
				/>
				<button @click="addToWhitelist" class="add-btn">添加到白名单</button>
			</view>
		</view>
		
		<!-- 申请授权列表 -->
		<view class="auth-requests-section">
			<view class="section-header">
				<text class="section-title">申请授权 ({{authRequests.length}})</text>
				<view class="filter-buttons">
					<button 
						@click="filterStatus = ''" 
						class="filter-btn" 
						:class="{ active: filterStatus === '' }"
					>
						全部
					</button>
					<button 
						@click="filterStatus = 'pending'" 
						class="filter-btn" 
						:class="{ active: filterStatus === 'pending' }"
					>
						待审核
					</button>
					<button 
						@click="filterStatus = 'approved'" 
						class="filter-btn" 
						:class="{ active: filterStatus === 'approved' }"
					>
						已批准
					</button>
					<button 
						@click="filterStatus = 'rejected'" 
						class="filter-btn" 
						:class="{ active: filterStatus === 'rejected' }"
					>
						已拒绝
					</button>
				</view>
			</view>
			
			<view class="auth-requests-list">
				<view v-for="request in filteredAuthRequests" :key="request.id" class="auth-request-item">
					<view class="request-info">
						<view class="request-header">
							<text class="user-nickname">{{request.nickname || '未知用户'}}</text>
							<text class="status-badge" :class="request.status">{{getStatusText(request.status)}}</text>
						</view>
						<text class="user-openid">{{request.openid}}</text>
						<text class="request-reason" v-if="request.reason">申请理由: {{request.reason}}</text>
						<text class="request-date">申请时间: {{formatDate(request.requested_at)}}</text>
						<text class="processed-info" v-if="request.processed_at">
							处理时间: {{formatDate(request.processed_at)}}
							<span v-if="request.processed_reason"> | 处理意见: {{request.processed_reason}}</span>
						</text>
					</view>
					<view class="request-actions" v-if="request.status === 'pending'">
						<button @click="processRequest(request.id, 'approved')" class="approve-btn">批准</button>
						<button @click="processRequest(request.id, 'rejected')" class="reject-btn">拒绝</button>
					</view>
				</view>
			</view>
			
			<!-- 空状态 -->
			<view v-if="filteredAuthRequests.length === 0" class="empty-state">
				<text class="empty-text">{{filterStatus ? '暂无符合条件的申请' : '暂无申请记录'}}</text>
			</view>
		</view>
		
		<!-- 白名单列表 -->
		<view class="list-section">
			<view class="list-header">
				<text class="list-title">白名单用户 ({{whitelist.length}})</text>
			</view>
			
			<view class="user-list">
				<view v-for="user in whitelist" :key="user.id" class="user-item">
					<view class="user-info">
						<text class="user-nickname">{{user.nickname || '未知用户'}}</text>
						<text class="user-openid">{{user.openid}}</text>
						<text class="user-date">添加时间: {{formatDate(user.added_at)}}</text>
					</view>
					<button @click="removeFromWhitelist(user.openid)" class="remove-btn">移除</button>
				</view>
			</view>
			
			<!-- 空状态 -->
			<view v-if="whitelist.length === 0" class="empty-state">
				<text class="empty-text">暂无白名单用户</text>
			</view>
		</view>
	</view>
</template>

<script>
	import config from '@/config.js'
	
	export default {
		data() {
			return {
				apiBaseUrl: config.apiBaseUrl,
				whitelist: [],
				authRequests: [],
				filterStatus: '',
				authCodes: [],
				newUser: {
					openid: '',
					nickname: ''
				}
			}
		},
		computed: {
			filteredAuthRequests() {
				if (!this.filterStatus) {
					return this.authRequests
				}
				return this.authRequests.filter(request => request.status === this.filterStatus)
			}
		},
		onLoad() {
			this.loadWhitelist()
			this.loadAuthRequests()
			this.loadAuthCodes()
		},
		methods: {
			// 加载白名单
			async loadWhitelist() {
				try {
					const token = uni.getStorageSync('token')
					const res = await uni.request({
						url: `${this.apiBaseUrl}/api/whitelist/list`,
						method: 'GET',
						header: {
							'Authorization': `Bearer ${token}`
						}
					})
					
					if (res.statusCode === 200) {
						this.whitelist = res.data.items || []
					} else {
						uni.showToast({
							title: '获取白名单失败',
							icon: 'none'
						})
					}
				} catch (error) {
					console.error('Load whitelist error:', error)
					uni.showToast({
						title: '网络错误',
						icon: 'none'
					})
				}
			},
			
			// 加载申请授权列表
			async loadAuthRequests() {
				try {
					const token = uni.getStorageSync('token')
					const res = await uni.request({
						url: `${this.apiBaseUrl}/api/auth-request/list`,
						method: 'GET',
						header: {
							'Authorization': `Bearer ${token}`
						}
					})
					
					if (res.statusCode === 200) {
						this.authRequests = res.data.items || []
					} else {
						uni.showToast({
							title: '获取申请列表失败',
							icon: 'none'
						})
					}
				} catch (error) {
					console.error('Load auth requests error:', error)
					uni.showToast({
						title: '网络错误',
						icon: 'none'
					})
				}
			},
			
			// 加载授权码
			async loadAuthCodes() {
				try {
					const token = uni.getStorageSync('token')
					const res = await uni.request({
						url: `${this.apiBaseUrl}/api/auth-codes`,
						method: 'GET',
						header: {
							'Authorization': `Bearer ${token}`
						}
					})
					
					if (res.statusCode === 200) {
						this.authCodes = res.data.auth_codes || []
					} else {
						uni.showToast({
							title: '获取授权码失败',
							icon: 'none'
						})
					}
				} catch (error) {
					console.error('Load auth codes error:', error)
					uni.showToast({
						title: '网络错误',
						icon: 'none'
					})
				}
			},
			
			// 添加到白名单
			async addToWhitelist() {
				if (!this.newUser.openid.trim()) {
					uni.showToast({
						title: '请输入openid',
						icon: 'none'
					})
					return
				}
				
				try {
					const token = uni.getStorageSync('token')
					const res = await uni.request({
						url: `${this.apiBaseUrl}/api/whitelist/add?openid=${encodeURIComponent(this.newUser.openid.trim())}&nickname=${encodeURIComponent(this.newUser.nickname.trim() || '')}`,
						method: 'POST',
						header: {
							'Authorization': `Bearer ${token}`,
							'Content-Type': 'application/json'
						}
					})
					
					if (res.statusCode === 200) {
						uni.showToast({
							title: '添加成功',
							icon: 'success'
						})
						this.newUser.openid = ''
						this.newUser.nickname = ''
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
								const token = uni.getStorageSync('token')
								const response = await uni.request({
									url: `${this.apiBaseUrl}/api/whitelist/remove/${openid}`,
									method: 'DELETE',
									header: {
										'Authorization': `Bearer ${token}`
									}
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
			},
			
			// 处理申请授权
			async processRequest(requestId, status) {
				const action = status === 'approved' ? '批准' : '拒绝'
				
				uni.showModal({
					title: `确认${action}`,
					content: `确定要${action}这个申请吗？`,
					success: async (res) => {
						if (res.confirm) {
							try {
								const token = uni.getStorageSync('token')
								const response = await uni.request({
									url: `${this.apiBaseUrl}/api/auth-request/${requestId}/process`,
									method: 'POST',
									data: {
										status: status,
										reason: ''
									},
									header: {
										'Authorization': `Bearer ${token}`,
										'Content-Type': 'application/json'
									}
								})
								
								if (response.statusCode === 200) {
									uni.showToast({
										title: `${action}成功`,
										icon: 'success'
									})
									this.loadAuthRequests()
									this.loadWhitelist()
								} else {
									uni.showToast({
										title: typeof response.data.detail === 'string' ? response.data.detail : `${action}失败`,
										icon: 'none'
									})
								}
							} catch (error) {
								console.error('Process request error:', error)
								uni.showToast({
									title: '网络错误',
									icon: 'none'
								})
							}
						}
					}
				})
			},
			
			// 获取状态文本
			getStatusText(status) {
				const statusMap = {
					'pending': '待审核',
					'approved': '已批准',
					'rejected': '已拒绝'
				}
				return statusMap[status] || status
			},
			
			// 格式化日期
			formatDate(dateString) {
				const date = new Date(dateString)
				return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
			}
		}
	}
</script>

<style>
	.whitelist-container {
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
	
	.auth-codes-section {
		background: #fff;
		padding: 30rpx;
		border-radius: 16rpx;
		margin-bottom: 20rpx;
	}
	
	.auth-codes-card {
		text-align: center;
	}
	
	.auth-codes-title {
		font-size: 30rpx;
		font-weight: bold;
		color: #333;
		display: block;
		margin-bottom: 10rpx;
	}
	
	.auth-codes-desc {
		font-size: 24rpx;
		color: #666;
		margin-bottom: 20rpx;
	}
	
	.auth-codes-list {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		gap: 15rpx;
	}
	
	.auth-code-item {
		background: #f0f0f0;
		padding: 10rpx 20rpx;
		border-radius: 8rpx;
		font-size: 26rpx;
		color: #333;
		border: 1rpx solid #e0e0e0;
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
	
	.auth-requests-section {
		background: #fff;
		border-radius: 16rpx;
		overflow: hidden;
		margin-bottom: 20rpx;
	}
	
	.section-header {
		padding: 30rpx;
		border-bottom: 1rpx solid #f0f0f0;
	}
	
	.section-title {
		font-size: 30rpx;
		font-weight: bold;
		color: #333;
		display: block;
		margin-bottom: 20rpx;
	}
	
	.filter-buttons {
		display: flex;
		gap: 15rpx;
	}
	
	.filter-btn {
		padding: 12rpx 20rpx;
		border: 1rpx solid #e0e0e0;
		border-radius: 6rpx;
		font-size: 24rpx;
		background: #fff;
		color: #666;
	}
	
	.filter-btn.active {
		background: #1AAD19;
		color: #fff;
		border-color: #1AAD19;
	}
	
	.auth-requests-list {
		padding: 0 30rpx;
	}
	
	.auth-request-item {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		padding: 30rpx 0;
		border-bottom: 1rpx solid #f0f0f0;
	}
	
	.auth-request-item:last-child {
		border-bottom: none;
	}
	
	.request-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 8rpx;
	}
	
	.request-header {
		display: flex;
		align-items: center;
		gap: 15rpx;
	}
	
	.user-nickname {
		font-size: 28rpx;
		font-weight: bold;
		color: #333;
	}
	
	.status-badge {
		padding: 4rpx 12rpx;
		border-radius: 12rpx;
		font-size: 22rpx;
		font-weight: bold;
	}
	
	.status-badge.pending {
		background: #FFF3CD;
		color: #FF9500;
	}
	
	.status-badge.approved {
		background: #D4EDDA;
		color: #1AAD19;
	}
	
	.status-badge.rejected {
		background: #F8D7DA;
		color: #FF3B30;
	}
	
	.user-openid {
		font-size: 24rpx;
		color: #666;
	}
	
	.request-reason {
		font-size: 26rpx;
		color: #333;
		line-height: 1.4;
	}
	
	.request-date {
		font-size: 22rpx;
		color: #999;
	}
	
	.processed-info {
		font-size: 22rpx;
		color: #999;
	}
	
	.request-actions {
		display: flex;
		flex-direction: column;
		gap: 10rpx;
	}
	
	.approve-btn {
		background: #1AAD19;
		color: #fff;
		padding: 12rpx 24rpx;
		border-radius: 6rpx;
		font-size: 24rpx;
	}
	
	.reject-btn {
		background: #FF3B30;
		color: #fff;
		padding: 12rpx 24rpx;
		border-radius: 6rpx;
		font-size: 24rpx;
	}
	
	.list-section {
		background: #fff;
		border-radius: 16rpx;
		overflow: hidden;
	}
	
	.list-header {
		padding: 30rpx;
		border-bottom: 1rpx solid #f0f0f0;
	}
	
	.list-title {
		font-size: 30rpx;
		font-weight: bold;
		color: #333;
	}
	
	.user-list {
		padding: 0 30rpx;
	}
	
	.user-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 30rpx 0;
		border-bottom: 1rpx solid #f0f0f0;
	}
	
	.user-item:last-child {
		border-bottom: none;
	}
	
	.user-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 8rpx;
	}
	
	.user-date {
		font-size: 22rpx;
		color: #999;
	}
	
	.remove-btn {
		background: #ff4757;
		color: #fff;
		padding: 12rpx 24rpx;
		border-radius: 6rpx;
		font-size: 24rpx;
	}
	
	.empty-state {
		padding: 60rpx 30rpx;
		text-align: center;
	}
	
	.empty-text {
		font-size: 28rpx;
		color: #999;
	}
</style> 