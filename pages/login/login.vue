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
	import request from '@/utils/request.js'
	
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
					const response = await request({
						url: '/auth/login',
						method: 'POST',
						data: {
							code: loginRes.code,
							nickname: userProfileRes.userInfo.nickName,
							avatar_url: userProfileRes.userInfo.avatarUrl
						},
						header: {
							'Content-Type': 'application/json'
						},
						timeout: 30000, // 设置30秒超时
						enableHttp2: true, // 启用HTTP2
						enableQuic: true, // 启用QUIC
						enableCache: false // 禁用缓存
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
							userId: response.data.user_id,
							nickname: userProfileRes.userInfo.nickName,
							avatarUrl: userProfileRes.userInfo.avatarUrl
						})
						
						// 使用reLaunch进行跳转
						try {
							// 先尝试关闭当前页面
							uni.hideLoading();
							
							// 使用reLaunch跳转
							uni.reLaunch({
								url: '/pages/index/index',
								success: () => {
									console.log('跳转成功');
								},
								fail: (err) => {
									console.error('reLaunch失败:', err);
									// 如果reLaunch失败，尝试使用redirectTo
									uni.redirectTo({
										url: '/pages/index/index',
										fail: (redirectErr) => {
											console.error('redirectTo也失败了:', redirectErr);
											// 最后尝试使用navigateTo
											uni.navigateTo({
												url: '/pages/index/index',
												fail: (navErr) => {
													console.error('所有跳转方式都失败了:', navErr);
													uni.showToast({
														title: '页面跳转失败，请重试',
														icon: 'none',
														duration: 2000
													});
												}
											});
										}
									});
								}
							});
						} catch (error) {
							console.error('跳转过程出错:', error);
							uni.showToast({
								title: '页面跳转失败，请重试',
								icon: 'none',
								duration: 2000
							});
						}
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
		min-height: 100vh;
		padding: 40rpx;
		background-color: #ffffff;
		box-sizing: border-box;
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