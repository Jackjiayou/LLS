<template>
	<view class="main-bg">

		
		<!-- 筛选条件 -->
		<view class="filter-section">
			<view class="filter-row">
				<picker mode="selector" :range="timeOptions" range-key="label" @change="onTimePickerChange">
					<view class="filter-item">
						<text class="filter-text">{{selectedTime}}</text>
						<uni-icons type="down" size="16" color="#666" />
					</view>
				</picker>
				<picker mode="selector" :range="scenarioOptions" range-key="label" @change="onScenarioPickerChange">
					<view class="filter-item">
						<text class="filter-text">{{selectedScenario}}</text>
						<uni-icons type="down" size="16" color="#666" />
					</view>
				</picker>
				<picker mode="selector" :range="sortOptions" range-key="label" @change="onSortPickerChange">
					<view class="filter-item">
						<text class="filter-text">{{selectedSort}}</text>
						<uni-icons type="down" size="16" color="#666" />
					</view>
				</picker>
			</view>
		</view>
		
		<!-- 当前用户排名 -->
		<view class="current-user-card" v-if="currentUserRank">
			<view class="user-rank-info">
				<image class="user-avatar" :src="currentUserRank.avatar || `${apiBaseUrl}/uploads/static/user-avatar.png`"></image>
				<view class="user-details">
					<text class="user-name">{{currentUserRank.name}}</text>
					<text class="user-desc">已练习场景{{currentUserRank.scenario_count}}个</text>
				</view>
				<view class="user-score">
					<text class="score-text">{{formatDuration(currentUserRank.score)}}{{getScoreUnit()}}</text>
				</view>
			</view>
		</view>
		
		<!-- 排行榜列表 -->
		<view class="ranking-list" v-if="rankingList.length > 0">
			<view class="list-content">
				<view v-for="(item, index) in rankingList" :key="item.user_id" class="ranking-item">
					<view class="rank-number">{{index + 1}}</view>
					<image class="user-avatar" :src="item.avatar || `${apiBaseUrl}/uploads/static/user-avatar.png`"></image>
					<view class="user-info">
						<text class="user-name">{{item.name}}</text>
						<text class="user-desc">已练习场景{{item.scenario_count}}个</text>
					</view>
					<view class="user-score">
						<text class="score-text">{{formatDuration(item.score)}}{{getScoreUnit()}}</text>
					</view>
				</view>
			</view>
		</view>
		
		<!-- 空状态 -->
		<view class="empty-state" v-else>
			<text class="empty-text">暂无数据</text>
		</view>
		

	</view>
</template>

<script>
	import config from '@/config.js'
	
	export default {
		data() {
			return {
				apiBaseUrl: config.apiBaseUrl,
				selectedTime: '今天',
				selectedScenario: '全部场景',
				selectedSort: '排名(按平均分)',
				rankingList: [],
				currentUserRank: null,
				
				// 选择器数据
				timeOptions: [
					{ label: '今天', value: 'today' },
					{ label: '本周', value: 'week' },
					{ label: '本月', value: 'month' },
					{ label: '全部', value: 'all' }
				],
				scenarioOptions: [
					{ label: '全部场景', value: 'all' },
					{ label: '营销沟通', value: '0' },
					{ label: '商务沟通', value: '1' },
					{ label: '商务谈判', value: '2' }
				],
				sortOptions: [
					{ label: '排名(按平均分)', value: 'avg_score' },
					{ label: '排名(按最高分)', value: 'max_score' },
					{ label: '排名(按总分)', value: 'total_score' },
					{ label: '排名(按时长)', value: 'duration' }
				],
				

				
				// 当前选中的值
				currentTimeValue: 'today',
				currentScenarioValue: 'all',
				currentSortValue: 'avg_score'
			}
		},
		onLoad() {
			console.log('排行榜页面加载');
			this.loadRankingData();
		},
		methods: {
			
			// 加载排行榜数据
			async loadRankingData() {
				try {
					console.log('开始加载排行榜数据');
					const token = uni.getStorageSync('token');
					const params = {
						time_period: this.currentTimeValue,
						scenario_id: this.currentScenarioValue,
						sort_by: this.currentSortValue
					};
					
					console.log('请求参数:', params);
					console.log('API地址:', `${this.apiBaseUrl}/api/ranking/list`);
					
					const res = await uni.request({
						url: `${this.apiBaseUrl}/api/ranking/list`,
						method: 'GET',
						data: params,
						header: {
							'Authorization': `Bearer ${token}`
						}
					});
					
					console.log('排行榜数据响应:', res);
					
					if (res.statusCode === 200) {
						this.rankingList = res.data.ranking_list || [];
						this.currentUserRank = res.data.current_user || null;
						console.log('排行榜数据加载成功:', this.rankingList);
					} else {
						console.error('Failed to fetch ranking data:', res);
						uni.showToast({
							title: '获取排行榜数据失败',
							icon: 'none'
						});
					}
				} catch (error) {
					console.error('Load ranking data error:', error);
					uni.showToast({
						title: '网络错误',
						icon: 'none'
					});
				}
			},
			
			// 时间选择器
			onTimePickerChange(e) {
				const index = e.detail.value;
				const selected = this.timeOptions[index];
				this.selectedTime = selected.label;
				this.currentTimeValue = selected.value;
				this.loadRankingData();
			},
			
			// 场景选择器
			onScenarioPickerChange(e) {
				const index = e.detail.value;
				const selected = this.scenarioOptions[index];
				this.selectedScenario = selected.label;
				this.currentScenarioValue = selected.value;
				this.loadRankingData();
			},
			
			// 排序选择器
			onSortPickerChange(e) {
				const index = e.detail.value;
				const selected = this.sortOptions[index];
				this.selectedSort = selected.label;
				this.currentSortValue = selected.value;
				this.loadRankingData();
			},

			// 根据排序方式获取分数单位
			getScoreUnit() {
				if (this.currentSortValue === 'avg_score') {
					return '分';
				} else if (this.currentSortValue === 'max_score') {
					return '分';
				} else if (this.currentSortValue === 'total_score') {
					return '分';
				} else if (this.currentSortValue === 'duration') {
					return '';
				}
				return '';
			},
			
			// 格式化时长显示
			formatDuration(seconds) {
				if (this.currentSortValue === 'duration') {
					const minutes = Math.floor(seconds / 60);
					const remainingSeconds = seconds % 60;
					if (minutes > 0) {
						return `${minutes}分${remainingSeconds}秒`;
					} else {
						return `${remainingSeconds}秒`;
					}
				}
				return seconds;
			}
		}
	}
</script>

<style>
	.main-bg {
		min-height: 100vh;
		background: #f7f7f7;
		padding: 20rpx 0 40rpx 0;
	}
	
	.filter-section {
		background: #fff;
		padding: 20rpx 24rpx;
		margin-bottom: 20rpx;
	}
	
	.filter-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.filter-item {
		display: flex;
		align-items: center;
		padding: 12rpx 20rpx;
		background: #f8f8f8;
		border-radius: 20rpx;
	}
	
	.filter-text {
		font-size: 26rpx;
		color: #333;
		margin-right: 8rpx;
	}
	
	.current-user-card {
		background: #f0f9ff;
		margin: 0 24rpx 20rpx 24rpx;
		border-radius: 16rpx;
		padding: 24rpx;
	}
	
	.user-rank-info {
		display: flex;
		align-items: center;
	}
	
	.user-avatar {
		width: 80rpx;
		height: 80rpx;
		border-radius: 40rpx;
		margin-right: 20rpx;
		background: #e5e5e5;
	}
	
	.user-details {
		flex: 1;
		display: flex;
		flex-direction: column;
	}
	
	.user-name {
		font-size: 28rpx;
		font-weight: bold;
		color: #222;
		margin-bottom: 8rpx;
	}
	
	.user-desc {
		font-size: 24rpx;
		color: #666;
	}
	
	.user-score {
		display: flex;
		align-items: center;
	}
	
	.score-text {
		font-size: 28rpx;
		font-weight: bold;
		color: #1AAD19;
	}
	
	.ranking-list {
		background: #fff;
		margin: 0 24rpx;
		border-radius: 16rpx;
		overflow: hidden;
	}
	
	.list-content {
		padding: 24rpx;
	}
	
	.ranking-item {
		display: flex;
		align-items: center;
		padding: 24rpx 0;
		border-bottom: 1rpx solid #f0f0f0;
	}
	
	.ranking-item:last-child {
		border-bottom: none;
	}
	
	.rank-number {
		width: 60rpx;
		height: 60rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 28rpx;
		font-weight: bold;
		color: #666;
		margin-right: 20rpx;
	}
	
	.ranking-item:nth-child(1) .rank-number {
		color: #FFD700;
	}
	
	.ranking-item:nth-child(2) .rank-number {
		color: #C0C0C0;
	}
	
	.ranking-item:nth-child(3) .rank-number {
		color: #CD7F32;
	}
	
	.user-info {
		flex: 1;
		display: flex;
		flex-direction: column;
	}
	
	.empty-state {
		display: flex;
		justify-content: center;
		align-items: center;
		height: 400rpx;
		background: #fff;
		margin: 0 24rpx;
		border-radius: 16rpx;
	}
	
	.empty-text {
		font-size: 28rpx;
		color: #999;
	}
	
	.picker-container {
		background: #fff;
		border-radius: 20rpx 20rpx 0 0;
	}
	
	.picker-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 30rpx;
		border-bottom: 1rpx solid #f0f0f0;
	}
	
	.picker-cancel, .picker-confirm {
		font-size: 28rpx;
		color: #666;
	}
	
	.picker-confirm {
		color: #1AAD19;
	}
	
	.picker-title {
		font-size: 30rpx;
		font-weight: bold;
		color: #222;
	}
	
	.picker-view {
		height: 400rpx;
	}
	
	.picker-item {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 80rpx;
		font-size: 28rpx;
		color: #333;
	}
</style> 