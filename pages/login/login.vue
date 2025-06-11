<template>
	<view class="login-container">
		<view class="logo">
			<image src="/static/logo.png" mode="aspectFit"></image>
		</view>
		<view class="title">欢迎使用</view>
		<view class="subtitle">请授权登录以继续使用</view>
		<button class="login-btn" @click="handleLogin">微信一键登录</button>
	</view>
</template>

<script>
	import config from '@/config.js'
	
	export default {
		data() {
			return {
				apiBaseUrl: config.apiBaseUrl
			}
		},
		methods: {
			async handleLogin() {
				console.log('开始登录流程')
				try {
					// 先获取用户信息
					const userProfileRes = await uni.getUserProfile({
						desc: '用于完善用户资料'
					})
					console.log('获取用户信息成功：', userProfileRes)
					
					// 获取微信登录凭证
					const loginRes = await uni.login({
						provider: 'weixin'
					})
					console.log('微信登录成功，返回：', loginRes)
					
					// 发送登录请求到后端
					const response = await uni.request({
						url: `${this.apiBaseUrl}/auth/login`,
						method: 'POST',
						data: {
							code: loginRes.code,
							nickname: userProfileRes.userInfo.nickName,
							avatar_url: userProfileRes.userInfo.avatarUrl
						},
						header: {
							'Content-Type': 'application/json'
						}
					})
					
					console.log('后端登录响应：', response)
					
					if (response.statusCode === 200 && response.data) {
						// 保存token
						uni.setStorageSync('token', response.data.access_token)
						// 保存token过期时间
						const expiresIn = response.data.expires_in || 7200
						const expireTime = Date.now() + expiresIn * 1000
						uni.setStorageSync('token_expire_time', expireTime)
						
						// 保存用户信息到本地
						uni.setStorageSync('userInfo', {
							nickname: userProfileRes.userInfo.nickName,
							avatarUrl: userProfileRes.userInfo.avatarUrl
						})
						
						// 跳转到首页
						uni.reLaunch({
							url: '/pages/index/index'
						})
					} else {
						console.error('登录失败：', response)
						uni.showToast({
							title: '登录失败：' + (response.data?.detail || '未知错误'),
							icon: 'none'
						})
					}
				} catch (error) {
					console.error('登录过程出错：', error)
					uni.showToast({
						title: '登录失败：' + (error.message || '未知错误'),
						icon: 'none'
					})
				}
			}
		}
	}
</script>

<style>
	.login-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100vh;
		padding: 40rpx;
		background-color: #f8f8f8;
	}
	
	.logo {
		width: 200rpx;
		height: 200rpx;
		margin-bottom: 40rpx;
	}
	
	.logo image {
		width: 100%;
		height: 100%;
	}
	
	.title {
		font-size: 40rpx;
		font-weight: bold;
		margin-bottom: 20rpx;
	}
	
	.subtitle {
		font-size: 28rpx;
		color: #666;
		margin-bottom: 60rpx;
	}
	
	.login-btn {
		width: 80%;
		height: 88rpx;
		line-height: 88rpx;
		background-color: #07c160;
		color: #fff;
		border-radius: 44rpx;
		font-size: 32rpx;
	}
</style> 