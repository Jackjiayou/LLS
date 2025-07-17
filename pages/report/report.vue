<template>
	<view class="container">
		<view class="report-header">
			<text class="report-title">练习报告</text>
			<text class="scene-name">{{sceneName}}</text>
		</view>
		
		<view class="report-content">
			<!-- 整体评分 -->
			<view class="score-section">
				<view class="overall-score">
					<text class="score-value">{{report.overall}}</text>
					<text class="score-label">总体评分</text>
				</view>
				
				<!-- 五维度评分雷达图 -->
				<view class="radar-chart">
					<canvas canvas-id="radarChart" id="radarChart" class="radar-canvas"></canvas>
				</view> 
				
				<!-- 各项评分 -->
				<view class="dimension-scores">
					<view class="dimension-item" v-for="(item, index) in report.dimensions" :key="index">
						<view class="dimension-bar-wrapper">
							<view class="dimension-name">{{item.name}}</view>
							<view class="dimension-bar-container">
								<view class="dimension-bar" :style="{width: item.score + '%'}">
									<text class="dimension-score">{{item.score}}</text>
								</view>
							</view>
						</view>
					</view>
				</view>
			</view>
			
			<!-- 详细分析 -->
			<view class="analysis-section">
				<view class="section-title">详细分析</view>
				
				<view class="analysis-item" v-for="(item, index) in report.analysis" :key="index">
					<view class="analysis-header">
						<view class="analysis-title">{{item.title}}</view>
						<view class="analysis-score">{{item.score}}分</view>
					</view>
					<view class="analysis-content">
						<text>{{item.content}}</text>
					</view>
				</view>
			</view>
			
			<!-- 改进建议 -->
			<view class="suggestion-section">
				<view class="section-title">改进建议</view>
				
				<view class="suggestion-list">
					<view class="suggestion-item" v-for="(item, index) in report.suggestions" :key="index">
						<view class="suggestion-icon">{{index + 1}}</view>
						<view class="suggestion-content">
							<text>{{item}}</text>
						</view>
					</view>
				</view>
			</view>
		</view>
		
		<view class="action-buttons">
			<button class="share-btn" @click="shareReport">分享报告</button>
			<button class="back-btn" @click="backToHome">返回首页</button>
		</view>
	</view>
</template>

<script>
	import uCharts from '@/uni_modules/qiun-data-charts/js_sdk/u-charts/u-charts.js';
	import config from '@/config.js'
	
	export default {
		data() {
			return {
				radarSize: 300, // 默认
				sceneId: 0,
				sceneName: '',
				apiBaseUrl: config.apiBaseUrl,
				report: {
					overall: 0,
					dimensions: [
						{ name: '语言组织能力', score: 0 },
						{ name: '说服力', score: 0 },
						{ name: '流利度', score: 0 },
						{ name: '发音准确度', score: 0 },
						{ name: '语音表达', score: 0 } 
					],
					analysis: [],
					suggestions: []
				}
			}
		},
        onLoad(options) {
            const practiceId = options.practiceId;
            const token = uni.getStorageSync('token');
            uni.request({
                url: `${this.apiBaseUrl}/api/report/analyze-practice`,
                method: 'POST',
                data: { practice_id: practiceId },
                header: {
                    'Authorization': `Bearer ${token}`, 
                    'Content-Type': 'application/json'
                },
                success: (res) => {
                    if (res.data && res.data.success) {
                        const d = res.data.data;
                        // 计算总体评分（平均分）
                        const overall = Math.round(
                            (d.organization.score + d.persuasiveness.score + d.fluency.score + d.pronunciation.score + d.expression.score) / 5
                        );
                        // 组装维度分数
                        const dimensions = [
                            { name: '语言组织能力', score: d.organization.score },
                            { name: '说服力', score: d.persuasiveness.score },
                            { name: '流利度', score: d.fluency.score },
                            { name: '发音准确度', score: d.pronunciation.score },
                            { name: '语音表达', score: d.expression.score }
                        ];
                        // 组装详细分析
                        const analysis = [
                            { title: '语言组织能力', score: d.organization.score, content: d.organization.analysis },
                            { title: '说服力', score: d.persuasiveness.score, content: d.persuasiveness.analysis },
                            { title: '流利度', score: d.fluency.score, content: d.fluency.analysis },
                            { title: '发音准确度', score: d.pronunciation.score, content: d.pronunciation.analysis },
                            { title: '语音表达', score: d.expression.score, content: d.expression.analysis }
                        ];
                        // 改进建议（如后端有单独字段可用，否则用分析文本）
                        const suggestions = [
                            d.organization.analysis,
                            d.persuasiveness.analysis,
                            d.fluency.analysis,
                            d.pronunciation.analysis,
                            d.expression.analysis
                        ];
                        this.report = {
                            overall,
                            dimensions,
                            analysis,
                            suggestions
                        };
                        this.initRadarChart();
                    } else {
                        uni.showToast({ title: '获取报告失败', icon: 'none' });
                    }
                }
            });
        },
		onReady() {
			const sysInfo = uni.getSystemInfoSync();
			this.radarSize = Math.floor(sysInfo.windowWidth * 0.9);
			this.initRadarChart();
		},
		methods: {
			initRadarChart() {
				const ctx = uni.createCanvasContext('radarChart', this);
				const size = this.radarSize || 300;
				const radarChart = new uCharts({
					type: 'radar',
					context: ctx,
					width: size,
					height: size,
					categories: this.report.dimensions.map(item => item.name),
					series: [{
						name: '评分',
						data: this.report.dimensions.map(item => item.score)
					}],
					animation: true,
					background: '#FFFFFF',
					padding: [size * 0.13, size * 0.13, size * 0.13, size * 0.13], // 13% padding，减小让图更居中
					legend: {
						show: false
					},
					radar: {
						gridType: 'radar',
						gridColor: '#ddd',
						gridCount: 4,
						labelColor: '#333',
						labelFontSize: Math.floor(size * 0.055), // 稍大
						splitArea: {
							show: true,
							areaStyle: {
								color: ['rgba(16,185,129,0.1)', 'rgba(16,185,129,0.2)', 'rgba(16,185,129,0.3)', 'rgba(16,185,129,0.4)']
							}
						},
						dataLabel: true,
						dataLabelColor: '#10b981',
						dataLabelFontSize: Math.floor(size * 0.045) // 稍大
					},
					extra: {
						radar: {
							linearType: 'custom',
							labelShow: true
						}
					}
				});
			},
			getReportData() {
				// 获取场景名称
				const sceneNames = {
                    0:'核苷酸介绍',
					1: '新客户开发',
					2: '异议处理',
					3: '产品推荐',
					4: '成交技巧'
				};
				this.sceneName = sceneNames[this.sceneId] || '未知场景';
				
				// 获取报告数据
				const reportId = uni.getStorageSync('latestReportId');
				if (reportId) {
					uni.showLoading({
						title: '加载报告...'
					});
					
					uni.request({
						url: `${this.apiBaseUrl}/api/reports/${reportId}`,
						success: (res) => {
							if (res.data) {
								console.log('获取报告成功:', res.data);
								
								// 格式化报告数据
								const reportData = res.data;
								const formattedReport = {
									overall: reportData.overall,
									dimensions: [
										{ name: '语言组织能力', score: reportData.dimensions.languageOrganization || 0 },
										{ name: '说服力', score: reportData.dimensions.persuasiveness || 0 },
										{ name: '流利度', score: reportData.dimensions.fluency || 0 },
										{ name: '准确度', score: reportData.dimensions.accuracy || 0 },
										{ name: '语言表达', score: reportData.dimensions.expression || 0 }
									],
									analysis: [
										{
											title: '语言组织能力',
											score: reportData.analysis.languageOrganization?.score || 0,
											content: reportData.analysis.languageOrganization?.content || ''
										},
										{
											title: '说服力',
											score: reportData.analysis.persuasiveness?.score || 0,
											content: reportData.analysis.persuasiveness?.content || ''
										},
										{
											title: '流利度',
											score: reportData.analysis.fluency?.score || 0,
											content: reportData.analysis.fluency?.content || ''
										},
										{
											title: '准确度',
											score: reportData.analysis.accuracy?.score || 0,
											content: reportData.analysis.accuracy?.content || ''
										},
										{
											title: '语言表达',
											score: reportData.analysis.expression?.score || 0,
											content: reportData.analysis.expression?.content || ''
										}
									],
									suggestions: reportData.suggestions || []
								};
								
								this.report = formattedReport;
								this.initRadarChart();
							}
						},
						fail: (err) => {
							console.error('获取报告失败:', err);
							uni.showToast({
								title: '获取报告失败',
								icon: 'none'
							});
						},
						complete: () => {
							uni.hideLoading();
						}
					});
				}
			},
			shareReport() {
				uni.showToast({
					title: '分享功能开发中',
					icon: 'none'
				});
			},
			backToHome() {
				uni.reLaunch({
					url: '/pages/index/index'
				});
			}
		}
	}
</script>
 

<style>
	.container {
		padding: 30rpx;
		display: flex;
		flex-direction: column;
		min-height: 100vh;
		box-sizing: border-box;
		background-color: #f5f5f5;
	}
	
	.report-header {
		background-color: #10b981;
		color: #fff;
		padding: 40rpx 30rpx;
		border-radius: 12rpx 12rpx 0 0;
		text-align: center;
		margin-bottom: 20rpx;
	}
	
	.report-title {
		font-size: 40rpx;
		font-weight: bold;
		margin-bottom: 10rpx;
		display: block;
	}
	
	.scene-name {
		font-size: 28rpx;
	}
	
	.report-content {
		flex: 1;
	}
	
	.score-section {
		background-color: #fff;
		border-radius: 12rpx;
		padding: 30rpx;
		margin-bottom: 20rpx;
	}
	
	.overall-score {
		text-align: center;
		margin-bottom: 30rpx;
	}
	
	.score-value {
		font-size: 80rpx;
		font-weight: bold;
		color: #10b981;
	}
	
	.score-label {
		font-size: 28rpx;
		color: #666;
		display: block;
	}
	
	.radar-chart {
		width: 90vw;
		height: 90vw;
		max-width: 700px;
		max-height: 700px;
		margin: 0 auto 30rpx auto;
		display: flex;
		justify-content: center;
		align-items: center;
	}
	
	.radar-canvas {
		width: 100%;
		height: 100%;
	}
	
	.dimension-scores {
		margin-top: 20rpx;
	}
	
	.dimension-item {
		margin-bottom: 15rpx;
	}
	
	.dimension-bar-wrapper {
		display: flex;
		align-items: center;
	}
	
	.dimension-name {
		width: 200rpx;
		font-size: 28rpx;
		color: #333;
	}
	
	.dimension-bar-container {
		flex: 1;
		height: 40rpx;
		background-color: #e0e0e0;
		border-radius: 20rpx;
		overflow: hidden;
	}
	
	.dimension-bar {
		height: 100%;
		background-color: #10b981;
		border-radius: 20rpx;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding-right: 10rpx;
	}
	
	.dimension-score {
		color: #fff;
		font-size: 24rpx;
	}
	
	.analysis-section, .suggestion-section {
		background-color: #fff;
		border-radius: 12rpx;
		padding: 30rpx;
		margin-bottom: 20rpx;
	}
	
	.section-title {
		font-size: 32rpx;
		font-weight: bold;
		margin-bottom: 20rpx;
		border-left: 6rpx solid #10b981;
		padding-left: 15rpx;
	}
	
	.analysis-item {
		margin-bottom: 30rpx;
		border-bottom: 1rpx solid #eee;
		padding-bottom: 20rpx;
	}
	
	.analysis-item:last-child {
		border-bottom: none;
		margin-bottom: 0;
		padding-bottom: 0;
	}
	
	.analysis-header { 
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 10rpx;
	}
	
	.analysis-title {
		font-size: 30rpx;
		font-weight: bold;
		color: #333;
	}
	
	.analysis-score {
		font-size: 30rpx;
		color: #10b981;
		font-weight: bold;
	}
	
	.analysis-content {
		font-size: 28rpx;
		color: #666;
		line-height: 1.5;
	}
	
	.suggestion-list {
		padding: 10rpx 0;
	}
	
	.suggestion-item {
		display: flex;
		margin-bottom: 20rpx;
	}
	
	.suggestion-icon {
		width: 50rpx;
		height: 50rpx;
		background-color: #10b981;
		color: #fff;
		border-radius: 25rpx;
		display: flex;
		justify-content: center;
		align-items: center;
		font-size: 28rpx;
		margin-right: 20rpx;
		flex-shrink: 0;
	}
	
	.suggestion-content {
		flex: 1;
		font-size: 28rpx;
		color: #666;
		line-height: 1.5;
	}
	
	.action-buttons {
		display: flex;
		justify-content: space-between;
		margin-top: 30rpx;
	}
	
	.share-btn, .back-btn {
		width: 48%;
		height: 80rpx;
		line-height: 80rpx;
		text-align: center;
		border-radius: 40rpx;
		font-size: 30rpx;
	}
	
	.share-btn {
		background-color: #10b981;
		color: #fff;
	}
	
	.back-btn {
		background-color: #f2f2f2;
		color: #333;
	}
</style> 