<template>
	<view class="main-bg">
		<!-- 顶部栏 -->
		<view class="top-bar">
			<text class="title">培训</text>
			<view class="top-icons">
				<uni-icons type="settings" size="24" color="#333" />
				<uni-icons type="more-filled" size="24" color="#333" style="margin-left: 16rpx;" />
			</view>
		</view>
		<!-- 用户信息卡片 -->
		<view class="card user-card">
			<image class="avatar" :src="userInfo.avatar"></image>
			<text class="username">{{userInfo.name}}</text>
			<view class="user-stats">
				<view class="stat-item">
					<text class="stat-value">{{stats.practice_count}}</text>
					<text class="stat-label">练习次数</text>
				</view>
				<view class="stat-item">
					<text class="stat-value">{{stats.total_duration}}h</text>
					<text class="stat-label">练习时长</text>
				</view>
				<view class="stat-item">
					<text class="stat-value">{{stats.scenario_count}}</text>
					<text class="stat-label">练习场景</text>
				</view>
			</view>
		</view>
		<!-- 功能入口卡片 -->   
		<view class="card func-card"> 
			<view class="func-item" @click="goToRanking"> 
				<image class="func-icon" :src="`${apiBaseUrl}/uploads/static/rank.png`"></image>
				<text class="func-label">排行榜</text>
			</view>
			<view class="func-item" @click="goToRecords">
				<image class="func-icon" :src="`${apiBaseUrl}/uploads/static/record.png`"></image>
				<text class="func-label">练习记录</text>
			</view>
			<view class="func-item" @click="goToDigitalHuman">
				<image class="func-icon" :src="`${apiBaseUrl}/uploads/static/digital-human.png`"></image>
				<text class="func-label">珍迪助手</text>
			</view>
		</view>
		<!-- 练习场景卡片 -->
		<view class="card scene-card">
			<view class="scene-title">练习场景</view>
			<view v-for="scene in scenes" :key="scene.id" class="scene-list-item" @click="goToScene(scene)">
				<image class="scene-list-icon" :src="scene.icon"></image>
				<view class="scene-list-info">
					<text class="scene-list-name">{{scene.name}}</text>
					<text class="scene-list-desc">{{scene.description}}</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import config from '@/config.js'
	
	export default {
		data() {
			return {
                stats: {
                        practice_count: 0,
                        total_duration: 0,
                        scenario_count: 0
                      },
                apiBaseUrl: config.apiBaseUrl,
				userInfo: {
					avatar: '',
					name: '未登录',
				},
				scenes: [
                    {
                    	id: 0,
                    	name: '核苷酸产品介绍',
                    	description: '赢得客户对核苷酸产品的认可',
                    	icon: ''
                    },
					{
						id: 1,
						name: '新客户开发',
						description: '针对首次接触的潜在客户，学习如何有效地介绍产品和建立信任',
						icon: ''
					},
					{
						id: 2,
						name: '异议处理',
						description: '学习如何面对客户提出的各种异议，并有效地进行回应',
						icon: ''
					},
					{
						id: 3,
						name: '产品推荐',
						description: '根据客户需求，推荐最合适的产品，提高销售成功率',
						icon: ''
					},
					// {
					// 	id: 4,
					// 	name: '成交技巧',
					// 	description: '学习如何引导客户做出购买决定，顺利完成销售',
					// 	icon: ''
					// }
				]
			}
		},
		onLoad() {
			console.log('Index page onLoad.');
			// 检查登录状态
			this.checkLoginStatus();
		},
		onShow() {
			console.log('Index page onShow.');
			// 每次页面显示时都检查登录状态
			this.checkLoginStatus();
		},
		methods: {
            async getPracticeStats() {
                  try {
                    const token = uni.getStorageSync('token');
                    const res = await uni.request({
                      url: `${this.apiBaseUrl}/practice/stats`,
                      method: 'GET',
                      header: {
                        'Authorization': `Bearer ${token}`
                      }
                    });
                    
                    if (res.statusCode === 200) {
                      this.stats = res.data;
                    } else {
                      console.error('Failed to fetch practice stats:', res);
                    }
                  } catch (error) {
                    console.error('Get practice stats caught error:', error);
                  }
                },
			async checkLoginStatus() {
				console.log('Checking login status...');
				const token = uni.getStorageSync('token');
				const tokenExpires = uni.getStorageSync('token_expire_time'); // 注意这里是 token_expire_time
				
				if (!token || !tokenExpires) {
					console.log('Token or expire time missing, redirecting to login.');
					// 未登录，跳转到登录页
					uni.redirectTo({
						url: '/pages/login/login',
						success: () => console.log('Redirected to login successfully.'),
						fail: (e) => console.error('Failed to redirect to login:', e)
					});
					return;
				}
				
				// 检查token是否过期
				const now = Date.now();
				const expireTime = Number(tokenExpires);
				
				if (now >= expireTime) {
					console.log('Token expired, attempting refresh...');
					// token过期，尝试刷新
					try {
						const res = await uni.request({
							url: `${this.apiBaseUrl}/auth/refresh-token`,
							method: 'POST',
							data: {
								token: token
							}
						});
						
						if (res.statusCode === 200) {
							console.log('Token refreshed successfully.');
							// 更新token
							uni.setStorageSync('token', res.data.access_token);
							uni.setStorageSync('token_expire_time', Date.now() + (res.data.expires_in || 7200) * 1000); // 确保更新过期时间
						} else {
							console.error('Token refresh failed:', res);
							// 刷新失败，跳转到登录页
							uni.redirectTo({
								url: '/pages/login/login',
								success: () => console.log('Redirected to login after refresh failure.'),
								fail: (e) => console.error('Failed to redirect to login after refresh failure:', e)
							});
							return;
						}
					} catch (error) {
						console.error('Token refresh caught error:', error);
						uni.redirectTo({
							url: '/pages/login/login',
							success: () => console.log('Redirected to login after refresh error.'),
							fail: (e) => console.error('Failed to redirect to login after refresh error:', e)
						});
						return;
					}
				}
				
				console.log('Login status good, getting user info and initializing scenes.');
				// 获取用户信息
				this.getUserInfo();
                await this.getPracticeStats();
				// 初始化图片路径
				this.scenes[0].icon = this.apiBaseUrl + '/uploads/static/scene1.png';
				this.scenes[1].icon = this.apiBaseUrl + '/uploads/static/scene2.png';
				this.scenes[2].icon = this.apiBaseUrl + '/uploads/static/scene3.png';
				this.scenes[3].icon = this.apiBaseUrl + '/uploads/static/scene4.png';
			},
			async getUserInfo() {
				console.log('Fetching user info...');
				try {
					const token = uni.getStorageSync('token');
					const res = await uni.request({
						url: `${this.apiBaseUrl}/auth/user-info`,
						method: 'GET',
						header: {
							'Authorization': `Bearer ${token}`
						}
					});
					
					if (res.statusCode === 200) {
						console.log('User info fetched successfully:', res.data);
						this.userInfo = {
							avatar: res.data.avatar_url || this.apiBaseUrl + '/uploads/static/user-avatar.png',
							name: res.data.nickname || '未设置昵称'
						};
					} else {
						console.error('Failed to fetch user info:', res);
					}
				} catch (error) {
					console.error('Get user info caught error:', error);
				}
			},
			getScenes() {
				console.log('Fetching scenes (using mock data).');
				// 从服务器获取场景数据
				// 这里使用模拟数据
				// uni.request({
				//   url: 'http://your-api-url/scenes',
				//   success: (res) => {
				//     this.scenes = res.data;
				//   }
				// });
			},
			goToScene(scene) {
				// 跳转到场景详情页
				uni.navigateTo({
					url: `/pages/scene/scene?id=${scene.id}`
				});
			},
			goToRanking() {
				// 跳转到排行榜页面
				uni.showToast({
					title: '排行榜功能开发中',
					icon: 'none'
				});
			},
			goToRecords() {
				// 跳转到练习记录页面
				uni.showToast({
					title: '练习记录功能开发中',
					icon: 'none'
				});
			},
			goToDigitalHuman() {
				// 跳转到珍迪助手页面
				uni.navigateTo({
					url: '/pages/assistant/assistant'
				});
			}
		}
	}
</script>

<style>
	.main-bg {
		min-height: 100vh;
		background: #f7f7f7;
		padding: 0 0 40rpx 0;
	}
	.top-bar {
		display: flex;
		justify-content: center;
		align-items: center;
		height: 100rpx;
		position: relative;
		background: #fff;
		margin-bottom: 20rpx;
	}
	.title {
		font-size: 32rpx;
		font-weight: bold;
		color: #222;
	}
	.top-icons {
		position: absolute;
		right: 30rpx;
		top: 50%;
		transform: translateY(-50%);
		display: flex;
		align-items: center;
	}
	.card {
		background: #fff;
		border-radius: 20rpx;
		box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.06);
		margin: 0 24rpx 24rpx 24rpx;
		padding: 32rpx 24rpx;
	}
	.user-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		margin-top: 10rpx;
	}
	.avatar {
		width: 120rpx;
		height: 120rpx;
		border-radius: 60rpx;
		margin-bottom: 16rpx;
		background: #e5e5e5;
	}
	.username {
		font-size: 34rpx;
		font-weight: bold;
		margin-bottom: 18rpx;
	}
	.user-stats {
		display: flex;
		width: 100%;
		justify-content: space-around;
		margin-top: 8rpx;
	}
	.stat-item {
		display: flex;
		flex-direction: column;
		align-items: center;
	}
	.stat-value {
		color: #1AAD19;
		font-size: 32rpx;
		font-weight: bold;
	}
	.stat-label {
		color: #888;
		font-size: 22rpx;
		margin-top: 4rpx;
	}
	.func-card {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 24rpx 24rpx;
	}
	.func-item {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 12rpx 0;
	}
	.func-icon {
		width: 64rpx;
		height: 64rpx;
		margin-bottom: 8rpx;
	}
	.func-label {
		font-size: 26rpx;
		color: #333;
	}
	.scene-card {
		padding: 24rpx 24rpx;
	}
	.scene-title {
		font-size: 28rpx;
		font-weight: bold;
		margin-bottom: 18rpx;
		color: #222;
	}
	.scene-list-item {
		display: flex;
		align-items: center;
		padding: 18rpx 0;
		border-bottom: 1rpx solid #f0f0f0;
	}
	.scene-list-item:last-child {
		border-bottom: none;
	}
	.scene-list-icon {
		width: 56rpx;
		height: 56rpx;
		margin-right: 18rpx;
	}
	.scene-list-info {
		display: flex;
		flex-direction: column;
	}
	.scene-list-name {
		font-size: 26rpx;
		font-weight: bold;
		color: #222;
	}
	.scene-list-desc {
		font-size: 22rpx;
		color: #888;
		margin-top: 4rpx;
	}
</style>
