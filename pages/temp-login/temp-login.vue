<template>
	<view class="temp-login-container">
		
		<view class="info-card">
			<text class="info-text">您不在授权用户列表中，此页面用于临时登录获取您的OpenID。</text>
			<text class="info-text">点击下方按钮授权并登录，获取OpenID后可以申请加入白名单。</text>
		</view>
		
		<view class="login-section" v-if="!loginResult">
			<button @click="tempLogin" class="login-btn" :disabled="isLoading">
				{{ isLoading ? '临时登录中...' : '授权并登录' }}
			</button>
		</view>
		
		<view v-if="loginResult" class="result-section">
			<view class="result-card">
				<text class="result-title">登录成功！</text>
				<view class="result-item">
					<text class="label">OpenID:</text>
					<text class="value openid">{{loginResult.openid}}</text>
					<button @click="copyOpenid" class="copy-btn">复制</button>
				</view>
				<!-- <view class="result-item">
					<text class="label">用户昵称:</text>
					<text class="value">{{loginResult.nickname || '未设置'}}</text>
				</view>
				<view class="result-item">
					<text class="label">用户ID:</text>
					<text class="value">{{loginResult.user_id}}</text>
				</view> -->
			</view>
			
			<!-- 申请授权区域 -->
			<view class="auth-request-section">
				<view class="auth-card">
					<text class="auth-title">申请授权</text>
					<text class="auth-desc">您可以直接申请加入白名单，管理员会审核您的申请。</text>
					<text class="auth-desc">如果您有授权码，请在申请理由中输入授权码即可自动通过并直接登录。</text>
					
					<view class="input-group">
						<input 
							v-model="authRequest.reason" 
							placeholder="请输入申请理由或授权码（可选）" 
							class="reason-input"
						/>
					</view>
					<view class="input-group">
						<input 
							v-model="authRequest.nickname" 
							placeholder="请输入用户名" 
							class="reason-input"
						/>
					</view>
					<button @click="submitAuthRequest" class="auth-btn" :disabled="isSubmitting">
						{{ isSubmitting ? '提交中...' : '申请授权' }}
					</button>
				</view>
			</view>
			
			<!-- 申请状态显示 -->
			<view v-if="authStatus" class="status-section">
				<view class="status-card">
					<text class="status-title">申请状态</text>
					<view class="status-item">
						<text class="label">状态:</text>
						<text class="value status" :class="authStatus.status">{{getStatusText(authStatus.status)}}</text>
					</view>
					<view class="status-item" v-if="authStatus.reason">
						<text class="label">申请理由:</text>
						<text class="value">{{authStatus.reason}}</text>
					</view>
					<view class="status-item" v-if="authStatus.processed_reason">
						<text class="label">处理意见:</text>
						<text class="value">{{authStatus.processed_reason}}</text>
					</view>
					<view class="status-item">
						<text class="label">申请时间:</text>
						<text class="value">{{formatDate(authStatus.requested_at)}}</text>
					</view>
				</view>
			</view>
			
			<view class="tips">
				<text class="tips-title">💡 下一步操作</text>
				<text class="tips-content">1. 复制上面的OpenID</text>
				<text class="tips-content">2. 联系管理员授权</text>
				<text class="tips-content">3. 或者直接点击"申请授权"按钮</text>
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
				isLoading: false,
				isSubmitting: false,
				loginResult: null,
				authRequest: {
					reason: ''
				},
				authStatus: null
			}
		},
		methods: {
			// 临时登录
			async tempLogin() {
				this.isLoading = true
				
				try {
					// 先获取用户信息
					let userInfo = {
						nickname: '',
						avatar_url: ''
					}
					
					try {
						const userProfileRes = await uni.getUserProfile({
							desc: '用于完善用户资料'
						})
						console.log('获取用户信息成功：', userProfileRes)
						userInfo = {
							nickname: userProfileRes.userInfo.nickName,
							avatar_url: userProfileRes.userInfo.avatarUrl
						}
					} catch (error) {
						console.log('获取用户信息失败，使用默认值:', error)
						// 如果获取失败，尝试使用其他方式
						try {
							const userInfoRes = await uni.getUserInfo({
								success: (res) => {
									userInfo = {
										nickname: res.userInfo.nickName || '',
										avatar_url: res.userInfo.avatarUrl || ''
									}
								}
							})
						} catch (err) {
							console.log('getUserInfo也失败了:', err)
						}
					}
					
					// 获取微信登录code
					const loginRes = await uni.login({
						provider: 'weixin'
					})
					
					if (loginRes.code) {
						// 调用临时登录API
						const res = await uni.request({
							url: `${this.apiBaseUrl}/auth/temp-login`,
							method: 'POST',
							data: {
								code: loginRes.code,
								nickname: userInfo.nickname,
								avatar_url: userInfo.avatar_url
							},
							header: {
								'Content-Type': 'application/json'
							}
						})
						
						if (res.statusCode === 200) {
							this.loginResult = {
								openid: res.data.openid,
								user_id: res.data.user_id,
								nickname: res.data.nickname || userInfo.nickname || ''
							}
							
							// 获取申请状态
							this.checkAuthStatus()
							
							uni.showToast({
								title: '登录成功',
								icon: 'success'
							})
						} else {
							uni.showToast({
								title: typeof res.data.detail === 'string' ? res.data.detail : '登录失败',
								icon: 'none'
							})
						}
					} else {
						uni.showToast({
							title: '获取微信登录码失败',
							icon: 'none'
						})
					}
				} catch (error) {
					console.error('Temp login error:', error)
					uni.showToast({
						title: '网络错误',
						icon: 'none'
					})
				} finally {
					this.isLoading = false
				}
			},
			
			// 复制openid
			copyOpenid() {
				uni.setClipboardData({
					data: this.loginResult.openid,
					success: () => {
						uni.showToast({
							title: 'OpenID已复制',
							icon: 'success'
						})
					}
				})
			},
			
			// 提交申请授权
			async submitAuthRequest() {
				if (!this.loginResult) {
					uni.showToast({
						title: '请先登录',
						icon: 'none'
					})
					return
				}
				
				this.isSubmitting = true
				
				try {
					const res = await uni.request({
						url: `${this.apiBaseUrl}/api/auth-request/create`,
						method: 'POST',
						data: {
							openid: this.loginResult.openid,
							nickname: this.authRequest.nickname,
							reason: this.authRequest.reason.trim()
						},
						header: {
							'Content-Type': 'application/json'
						}
					})
					
					if (res.statusCode === 200) {
						// 检查是否是授权码自动批准
						if (res.data.status === 'approved' && res.data.processed_by === 'system') {
							// 授权码自动批准，直接登录
							uni.showToast({
								title: '授权码验证成功，正在登录...',
								icon: 'success'
							})
							
							// 延迟一下让用户看到提示
							setTimeout(async () => {
								await this.autoLogin()
							}, 1500)
						} else {
							// 普通申请，等待管理员审核
							uni.showToast({
								title: '申请提交成功',
								icon: 'success'
							})
							this.authRequest.reason = ''
							this.checkAuthStatus()
						}
					} else {
						uni.showToast({
							title: typeof res.data.detail === 'string' ? res.data.detail : '申请提交失败',
							icon: 'none'
						})
					}
				} catch (error) {
					console.error('Submit auth request error:', error)
					uni.showToast({
						title: '网络错误',
						icon: 'none'
					})
				} finally {
					this.isSubmitting = false
				}
			},
			
			// 自动登录
			async autoLogin() {
				try {
					// 获取微信登录code
					const loginRes = await uni.login({
						provider: 'weixin'
					})
					
					if (loginRes.code) {
						// 获取用户信息
						let userInfo = {
							nickname: this.loginResult.nickname || '',
							avatar_url: ''
						}
						
						try {
							const userProfileRes = await uni.getUserProfile({
								desc: '用于完善用户资料'
							})
							userInfo = {
								nickname: userProfileRes.userInfo.nickName,
								avatar_url: userProfileRes.userInfo.avatarUrl
							}
						} catch (error) {
							console.log('获取用户信息失败，使用已有信息:', error)
						}
						
						// 调用正式登录API
						const res = await uni.request({
							url: `${this.apiBaseUrl}/auth/login`,
							method: 'POST',
							data: {
								code: loginRes.code,
								nickname: userInfo.nickname,
								avatar_url: userInfo.avatar_url
							},
							header: {
								'Content-Type': 'application/json'
							}
						})
						
						if (res.statusCode === 200 && res.data) {
							// 保存token
							uni.setStorageSync('token', res.data.access_token)
							// 保存token过期时间
							const expiresIn = res.data.expires_in || 7200
							const expireTime = Date.now() + expiresIn * 1000
							uni.setStorageSync('token_expire_time', expireTime)
							
							// 保存用户信息到本地
							uni.setStorageSync('userInfo', {
								userId: res.data.user_id,
								nickname: userInfo.nickname,
								avatarUrl: userInfo.avatar_url
							})
							
							uni.showToast({
								title: '登录成功',
								icon: 'success'
							})
							
							// 跳转到首页
							setTimeout(() => {
								uni.reLaunch({
									url: '/pages/index/index',
									success: () => {
										console.log('跳转到首页成功')
									},
									fail: (err) => {
										console.error('跳转失败:', err)
										uni.redirectTo({
											url: '/pages/index/index'
										})
									}
								})
							}, 1000)
						} else {
							uni.showToast({
								title: '自动登录失败',
								icon: 'none'
							})
						}
					} else {
						uni.showToast({
							title: '获取登录码失败',
							icon: 'none'
						})
					}
				} catch (error) {
					console.error('Auto login error:', error)
					uni.showToast({
						title: '自动登录失败',
						icon: 'none'
					})
				}
			},
			
			// 检查申请状态
			async checkAuthStatus() {
				if (!this.loginResult) return
				
				try {
					const res = await uni.request({
						url: `${this.apiBaseUrl}/api/auth-request/my?openid=${encodeURIComponent(this.loginResult.openid)}`,
						method: 'GET'
					})
					
					if (res.statusCode === 200) {
						this.authStatus = res.data
					} else if (res.statusCode === 404) {
						this.authStatus = null
					}
				} catch (error) {
					console.error('Check auth status error:', error)
				}
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
	.temp-login-container {
		min-height: 100vh;
		background: #f7f7f7;
		padding: 20rpx;
	}
	
	.header {
		background: #fff;
		padding: 40rpx 30rpx;
		border-radius: 16rpx;
		margin-bottom: 20rpx;
		text-align: center;
	}
	
	.title {
		font-size: 36rpx;
		font-weight: bold;
		color: #333;
		display: block;
		margin-bottom: 10rpx;
	}
	
	.subtitle {
		font-size: 26rpx;
		color: #666;
	}
	
	.info-card {
		background: #e8f5e8;
		padding: 30rpx;
		border-radius: 16rpx;
		margin-bottom: 20rpx;
	}
	
	.info-text {
		font-size: 26rpx;
		color: #1AAD19;
		line-height: 1.5;
	}
	
	.login-section {
		padding: 40rpx 0;
	}
	
	.login-btn {
		background: #1AAD19;
		color: #fff;
		padding: 30rpx;
		border-radius: 12rpx;
		font-size: 32rpx;
		width: 100%;
	}
	
	.login-btn:disabled {
		background: #ccc;
	}
	
	.result-section {
		margin-top: 40rpx;
	}
	
	.result-card {
		background: #fff;
		padding: 30rpx;
		border-radius: 16rpx;
		margin-bottom: 20rpx;
	}
	
	.result-title {
		font-size: 30rpx;
		font-weight: bold;
		color: #1AAD19;
		display: block;
		margin-bottom: 20rpx;
		text-align: center;
	}
	
	.result-item {
		display: flex;
		align-items: center;
		padding: 20rpx 0;
		border-bottom: 1rpx solid #f0f0f0;
	}
	
	.result-item:last-child {
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
	
	.auth-request-section {
		margin-bottom: 20rpx;
	}
	
	.auth-card {
		background: #fff;
		padding: 30rpx;
		border-radius: 16rpx;
	}
	
	.auth-title {
		font-size: 30rpx;
		font-weight: bold;
		color: #333;
		display: block;
		margin-bottom: 15rpx;
	}
	
	.auth-desc {
		font-size: 26rpx;
		color: #666;
		line-height: 1.5;
		margin-bottom: 20rpx;
	}
	
	.input-group {
		margin-bottom: 20rpx;
	}
	
	.reason-input {
		padding: 20rpx;
		border: 1rpx solid #e0e0e0;
		border-radius: 8rpx;
		font-size: 28rpx;
		width: 100%;
		box-sizing: border-box;
		min-height: 80rpx;
	}
	
	.auth-btn {
		background: #007AFF;
		color: #fff;
		padding: 25rpx;
		border-radius: 12rpx;
		font-size: 30rpx;
		width: 100%;
	}
	
	.auth-btn:disabled {
		background: #ccc;
	}
	
	.status-section {
		margin-bottom: 20rpx;
	}
	
	.status-card {
		background: #fff;
		padding: 30rpx;
		border-radius: 16rpx;
	}
	
	.status-title {
		font-size: 30rpx;
		font-weight: bold;
		color: #333;
		display: block;
		margin-bottom: 20rpx;
		text-align: center;
	}
	
	.status-item {
		display: flex;
		align-items: flex-start;
		padding: 15rpx 0;
		border-bottom: 1rpx solid #f0f0f0;
	}
	
	.status-item:last-child {
		border-bottom: none;
	}
	
	.status {
		font-weight: bold;
	}
	
	.status.pending {
		color: #FF9500;
	}
	
	.status.approved {
		color: #1AAD19;
	}
	
	.status.rejected {
		color: #FF3B30;
	}
	
	.tips {
		background: #fff3cd;
		padding: 30rpx;
		border-radius: 16rpx;
	}
	
	.tips-title {
		font-size: 28rpx;
		font-weight: bold;
		color: #856404;
		display: block;
		margin-bottom: 15rpx;
	}
	
	.tips-content {
		font-size: 26rpx;
		color: #856404;
		line-height: 1.6;
		display: block;
		margin-bottom: 8rpx;
	}
</style> 