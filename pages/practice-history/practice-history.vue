<template>
	<view class="container">

		
		<!-- 练习记录列表 -->
		<scroll-view class="history-list" :scroll-y="true">
			<view v-for="(practice, index) in practiceList" :key="index" class="practice-item" @click="viewReport(practice)" @longpress="deletePractice(practice)">
				<view class="practice-content">
					<view class="practice-info">
						<text class="scene-name">{{practice.sceneName}}</text>
						<text class="practice-duration">练习{{formatDuration(practice.duration)}}</text>
						<text class="practice-date">日期: {{practice.createdAt}}</text>
					</view>
					<view class="practice-score" v-if="practice.hasReport && practice.overallScore > 0">
						<text class="score-value">{{practice.overallScore}}</text>
						<text class="score-label">分</text>
						<view class="score-arrow">></view>
					</view>
					<view class="practice-status" v-else>
						<text class="status-text" :class="{
							'in-progress': practice.status === 'in-progress',
							'completed': practice.status === 'completed',
							'paused': practice.status === 'paused',
							'cancelled': practice.status === 'cancelled'
						}">{{practice.statusText}}</text>
					</view>
				</view>
			</view>
			
			<!-- 加载更多 -->
			<view v-if="loading" class="loading-more">
				<view class="loading-spinner"></view>
				<text class="loading-text">加载中...</text>
			</view>
			
			<!-- 无数据提示 -->
			<view v-if="practiceList.length === 0 && !loading" class="empty-state">
				<view class="empty-icon">
					<view class="empty-icon-circle"></view>
					<view class="empty-icon-line"></view>
				</view>
				<text class="empty-title">暂无练习记录</text>
				<text class="empty-desc">开始你的第一次练习，提升沟通技巧吧！</text>
				<button class="start-practice-btn" @click="goToScene">开始练习</button>
			</view>
		</scroll-view>
	</view>
</template>

<script>
	import config from '@/config.js'
	
	export default {
		data() {
			return {
				practiceList: [],
				loading: false,
				apiBaseUrl: config.apiBaseUrl,
				page: 1,
				hasMore: true
			}
		},
		onLoad() {
			this.loadPracticeHistory();
		},
		onPullDownRefresh() {
			this.refreshData();
			uni.showToast({
				title: '刷新成功',
				icon: 'success',
				duration: 1500
			});
		},
		onReachBottom() {
			if (this.hasMore && !this.loading) {
				this.loadMoreData();
			}
		},
		methods: {
			loadPracticeHistory() {
				if (this.loading) return;
				
				this.loading = true;
				const token = uni.getStorageSync('token');
				const header = {
					'Authorization': `Bearer ${token}`,
					'Content-Type': 'application/json'
				};

				uni.request({
					url: this.apiBaseUrl + '/api/report/practice/history',
					method: 'GET',
					data: { page: this.page, limit: 10 },
					header,
					success: (res) => {
						if (res.data && res.data.success) {
							const newPractices = res.data.data.practices || [];
							if (this.page === 1) {
								this.practiceList = newPractices;
							} else {
								this.practiceList = [...this.practiceList, ...newPractices];
							}
							this.hasMore = newPractices.length === 10;
						} else {
							uni.showToast({ title: '获取练习历史失败', icon: 'none' });
						}
					},
					fail: (err) => {
						console.error('获取练习历史失败:', err);
						uni.showToast({ title: '获取练习历史失败', icon: 'none' });
					},
					complete: () => {
						this.loading = false;
						uni.stopPullDownRefresh();
					}
				});
			},
			refreshData() {
				this.page = 1;
				this.hasMore = true;
				this.loadPracticeHistory();
			},
			loadMoreData() {
				this.page++;
				this.loadPracticeHistory();
			},
			viewReport(practice) {
				// 检查是否有报告数据（通过三个独立字段判断）
				const hasReportData = practice.organizationScore > 0 || 
				                    practice.persuasivenessScore > 0 || 
				                    practice.fluencyScore > 0 || 
				                    practice.pronunciationScore > 0 || 
				                    practice.expressionScore > 0;
				
				if (hasReportData) {
					// 有报告数据，直接查看
					uni.navigateTo({
						url: `/pages/report/report?practiceId=${practice.practiceId}&conversationId=${practice.conversationId}&sceneId=${practice.sceneId}&fromChat=false`
					});
				} else {
					// 没有报告数据，重新生成
					uni.navigateTo({
						url: `/pages/report/report?practiceId=${practice.practiceId}&conversationId=${practice.conversationId}&sceneId=${practice.sceneId}&fromChat=false&generateNew=true`
					});
				}
			},
			formatDuration(seconds) {
				if (!seconds || seconds === 0) return '0秒';
				if (seconds < 60) return `${seconds}秒`;
				const minutes = Math.floor(seconds / 60);
				const remainingSeconds = seconds % 60;
				if (remainingSeconds === 0) return `${minutes}分钟`;
				return `${minutes}分${remainingSeconds}秒`;
			},
			deletePractice(practice) {
				uni.showModal({
					title: '确认删除',
					content: '长按删除：确定要删除这条练习记录吗？删除后无法恢复。',
					confirmText: '删除',
					confirmColor: '#ff4757',
					cancelText: '取消',
					success: (res) => {
						if (res.confirm) {
							this.performDelete(practice);
						}
					}
				});
			},
			performDelete(practice) {
				const token = uni.getStorageSync('token');
				const header = {
					'Authorization': `Bearer ${token}`,
					'Content-Type': 'application/json'
				};

				uni.request({
					url: this.apiBaseUrl + `/api/report/practice/${practice.practiceId}`,
					method: 'DELETE',
					header,
					success: (res) => {
						if (res.data && res.data.success) {
							uni.showToast({
								title: '删除成功',
								icon: 'success',
								duration: 1500
							});
							// 从列表中移除被删除的记录
							this.practiceList = this.practiceList.filter(item => item.practiceId !== practice.practiceId);
						} else {
							uni.showToast({
								title: res.data?.message || '删除失败',
								icon: 'none'
							});
						}
					},
					fail: (err) => {
						console.error('删除练习记录失败:', err);
						uni.showToast({
							title: '删除失败',
							icon: 'none'
						});
					}
				});
			},
			goToScene() {
				uni.navigateTo({
					url: '/pages/scene/scene?id=0'
				});
			}
		}
	}
</script>

<style>
	.container {
		display: flex;
		flex-direction: column;
		height: 100vh;
		background-color: #f8fafc;
	}
	
	.header {
		background: linear-gradient(135deg, #10b981 0%, #059669 100%);
		color: #ffffff;
		padding: 40rpx 32rpx 32rpx;
		text-align: center;
		box-shadow: 0 2rpx 8rpx rgba(16, 185, 129, 0.15);
	}
	
	.title {
		font-size: 34rpx;
		font-weight: 600;
		letter-spacing: 0.5rpx;
	}
	
	.history-list {
		flex: 1;
		padding: 20rpx;
	}
	
	.practice-item {
		background-color: #ffffff;
		border-radius: 12rpx;
		padding: 24rpx;
		margin-bottom: 16rpx;
		box-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.08);
		border: 1rpx solid #f0f0f0;
		transition: all 0.2s ease;
		cursor: pointer;
	}

	.practice-item:active {
		background-color: #f8f9fa;
		transform: scale(0.98);
	}
	
	.practice-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.practice-info {
		flex: 1;
	}
	
	.scene-name {
		font-size: 30rpx;
		font-weight: 600;
		color: #333333;
		display: block;
		margin-bottom: 8rpx;
		line-height: 1.4;
	}
	
	.practice-duration {
		font-size: 24rpx;
		color: #666666;
		margin-bottom: 6rpx;
		display: block;
	}
	
	.practice-date {
		font-size: 22rpx;
		color: #999999;
		display: block;
	}
	
	.practice-score {
		text-align: right;
		display: flex;
		align-items: center;
	}
	
	.score-value {
		font-size: 40rpx;
		font-weight: 700;
		color: #10b981;
		margin-right: 4rpx;
	}

	.score-label {
		font-size: 20rpx;
		color: #10b981;
		font-weight: 500;
		margin-right: 8rpx;
	}

	.score-arrow {
		font-size: 20rpx;
		color: #10b981;
		font-weight: 600;
	}
	
	.practice-status {
		text-align: center;
	}

	.status-text {
		font-size: 20rpx;
		color: #666666;
		padding: 6rpx 12rpx;
		border-radius: 6rpx;
		background-color: #f5f5f5;
		font-weight: 500;
		border: 1rpx solid #e0e0e0;
	}

	.status-text.in-progress {
		background-color: #fff3cd;
		color: #856404;
		border-color: #ffeaa7;
	}

	.status-text.completed {
		background-color: #d4edda;
		color: #155724;
		border-color: #c3e6cb;
	}

	.status-text.paused {
		background-color: #f8d7da;
		color: #721c24;
		border-color: #f5c6cb;
	}

	.status-text.cancelled {
		background-color: #e2e3e5;
		color: #383d41;
		border-color: #d6d8db;
	}
	
	.loading-more {
		text-align: center;
		padding: 40rpx;
		color: #64748b;
		font-size: 26rpx;
	}
	
	.loading-spinner {
		width: 32rpx;
		height: 32rpx;
		border: 3rpx solid #f1f5f9;
		border-top: 3rpx solid #10b981;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 12rpx;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.loading-text {
		font-size: 26rpx;
		font-weight: 500;
	}
	
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 100rpx 40rpx;
		background: #ffffff;
		border-radius: 20rpx;
		box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
		margin: 40rpx 20rpx;
		border: 1rpx solid #f1f5f9;
	}

	.empty-icon {
		width: 100rpx;
		height: 100rpx;
		margin-bottom: 32rpx;
		position: relative;
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.empty-icon-circle {
		width: 100%;
		height: 100%;
		border-radius: 50%;
		border: 3rpx solid #e2e8f0;
		box-sizing: border-box;
		position: relative;
		background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
	}

	.empty-icon-line {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 50%;
		height: 2rpx;
		background: linear-gradient(90deg, #10b981 0%, #059669 100%);
		border-radius: 1rpx;
	}

	.empty-icon-line::before {
		content: '';
		position: absolute;
		top: -6rpx;
		left: 50%;
		transform: translateX(-50%);
		width: 2rpx;
		height: 16rpx;
		background: linear-gradient(180deg, #10b981 0%, #059669 100%);
		border-radius: 1rpx;
	}

	.empty-title {
		font-size: 32rpx;
		font-weight: 600;
		color: #1e293b;
		margin-bottom: 12rpx;
		text-align: center;
	}

	.empty-desc {
		font-size: 26rpx;
		color: #64748b;
		text-align: center;
		margin-bottom: 48rpx;
		line-height: 1.6;
	}

	.start-practice-btn {
		background: linear-gradient(135deg, #10b981 0%, #059669 100%);
		color: #ffffff;
		padding: 20rpx 40rpx;
		border-radius: 12rpx;
		font-size: 28rpx;
		font-weight: 600;
		border: none;
		box-shadow: 0 2rpx 8rpx rgba(16, 185, 129, 0.25);
		transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.start-practice-btn:active {
		transform: translateY(1rpx);
		box-shadow: 0 1rpx 4rpx rgba(16, 185, 129, 0.3);
	}
</style> 