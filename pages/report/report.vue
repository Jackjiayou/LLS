<template>
	<view class="container">
		<view class="report-header">
			<text class="report-title">练习报告</text>
			<text class="scene-name">{{sceneName}}</text>
		</view>
        
		<view class="report-content">
			<!-- 整体评分 -->
			<view class="score-section vertical">
				<view class="overall-score">
					<text class="score-value">{{report.overall}}</text>
					<text class="score-label">总体评分</text>
				</view>
				<view class="radar-chart">
					<view v-if="loading" class="loading-container">
						<text class="loading-text">分析中...</text>
					</view>
					<uni-ec-canvas v-else class="radar-canvas" id="radar-canvas" ref="canvas" canvas-id="radar-canvas" :ec="ec"></uni-ec-canvas>
				</view>
			</view>
			
			<!-- 详细分析 -->
			<view class="analysis-section">
				<view class="section-title">详细分析</view>
				<!-- 横向评分维度导航 -->
				<scroll-view class="dimension-nav" scroll-x="true" :scroll-into-view="navScrollIntoView" show-scrollbar="false">
					<view 
						v-for="(item, index) in report.analysis" 
						:key="index" 
						class="dimension-nav-item"
						:id="'nav-item-' + index"
						:class="{active: activeAnalysisIndex === index}"
						@click="scrollToAnalysis(index)"
					>
						{{item.title}}
					</view>
				</scroll-view>
				<!-- 详细分析内容 -->
				<view>
					<view 
						class="analysis-item" 
						v-for="(item, index) in report.analysis" 
						:key="index"
						:id="'analysis-' + index"
					>
						<view class="analysis-header">
							<view class="analysis-title">{{item.title}}</view>
							<view class="analysis-score">{{item.score}}分</view>
						</view>
						<view class="analysis-content">
							<text>{{item.content}}</text>
						</view>
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
	import uniEcCanvas from '@/uni_modules/uni-ec-canvas/uni-ec-canvas.vue';
	import * as echarts from '@/uni_modules/uni-ec-canvas/echarts';
	import config from '@/config.js' 
	
	let chart = null;

	export default {
		components: { uniEcCanvas },
		data() {
			return {
				ec: { lazyLoad: true },
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
				},
				activeAnalysisIndex: 0,
				navScrollIntoView: '',
				loading: false
			}
		},
        onLoad(options) {
            this.loading = true;
            uni.showLoading({ title: '音频合并中...' });
            const conversationId = options.conversationId;
            const practiceId = options.practiceId;
            const token = uni.getStorageSync('token');
            const header = {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            };

            // 1. 先调用音频合并接口
            uni.request({
                url: this.apiBaseUrl + '/api/report/combine-audio',
                method: 'POST',
                data: { practice_id: practiceId, conversationId },
                header,
                success: (res) => {
                    if (res.data && res.data.success) {
                        // 合并成功，拿到 file_path
                        const filePath = res.data.file_path;
                        uni.hideLoading();
                        
                        // 2. 并发调用两个分析接口
                        uni.showLoading({ title: '分析中...' });
                        Promise.all([
                            this.fetchOrganization('/api/report/analyze-organization', { practice_id: practiceId, conversationId, output_path: filePath }, header),
                            this.fetchPersuasiveness('/api/report/analyze-persuasiveness', { practice_id: practiceId, conversationId, output_path: filePath }, header),
                            this.fetchFluencyExpressionPronunciation('/api/report/analyze-fluency-expression-pronunciation', { practice_id: practiceId, conversationId, output_path: filePath }, header)
                        ]).then(([org, pers, fluExpPron]) => {
                            // 组装数据
                            const overall = Math.round(
                                (org.score + pers.score + fluExpPron.fluency.score + fluExpPron.pronunciation.score + fluExpPron.expression.score) / 5
                            );
                            const dimensions = [
                                { name: '语言组织能力', score: org.score },
                                { name: '说服力', score: pers.score },
                                { name: '流利度', score: fluExpPron.fluency.score },
                                { name: '发音准确度', score: fluExpPron.pronunciation.score },
                                { name: '语音表达', score: fluExpPron.expression.score }
                            ];
                            const analysis = [
                                { title: '语言组织能力', score: org.score, content: org.analysis },
                                { title: '说服力', score: pers.score, content: pers.analysis },
                                { title: '流利度', score: fluExpPron.fluency.score, content: fluExpPron.fluency.analysis },
                                { title: '发音准确度', score: fluExpPron.pronunciation.score, content: fluExpPron.pronunciation.analysis },
                                { title: '语音表达', score: fluExpPron.expression.score, content: fluExpPron.expression.analysis }
                            ];
                            const suggestions = [
                                org.analysis, pers.analysis, fluExpPron.fluency.analysis, fluExpPron.pronunciation.analysis, fluExpPron.expression.analysis
                            ];
                            this.report = { overall, dimensions, analysis, suggestions };
                            
                            // 所有数据返回后显示雷达图
                            this.$nextTick(() => {
                                if (this.$refs.canvas) {
                                    this.$refs.canvas.init(this.initChart);
                                }
                            });
                        }).catch(err => {
                            uni.showToast({ title: '获取报告失败', icon: 'none' });
                        }).finally(() => {
                            this.loading = false;
                            uni.hideLoading();
                        });
                    } else {
                        uni.showToast({ title: '音频合并失败', icon: 'none' });
                        this.loading = false;
                        uni.hideLoading();
                    }
                },
                fail: () => {
                    uni.showToast({ title: '音频合并失败', icon: 'none' });
                    this.loading = false;
                    uni.hideLoading();
                }
            });
        },
		onReady() {
			// 初始化echarts雷达图 - 只在数据加载完成后调用
			// this.$refs.canvas.init(this.initChart);
		},
		methods: {  
			initChart(canvas, width, height, dpr) {
				if (!canvas) {
					console.warn('Canvas is not available');
					return;
				}
				chart = echarts.init(canvas, null, {
					width: width,
					height: height,
					devicePixelRatio: dpr
				});
				canvas.setChart(chart);
				// 动态生成雷达图option
				const indicators = this.report.dimensions.map(item => ({ name: item.name, max: 100 }));
				const values = this.report.dimensions.map(item => item.score);
				const option = {
					title: {
					
						left: 'center',
						top: 10,
						textStyle: {
							fontSize: 16
						}
					},
					tooltip: {},
					radar: {
						indicator: indicators,
						radius: '70%',
						splitNumber: 4,
						shape: 'polygon',
						splitArea: {
							areaStyle: {
								color: ['rgba(16,185,129,0.1)', 'rgba(16,185,129,0.2)', 'rgba(16,185,129,0.3)', 'rgba(16,185,129,0.4)']
							}
						},
						axisLine: {
							lineStyle: {
								color: '#10b981'
							}
						},
						splitLine: {
							lineStyle: {
								color: '#10b981'
							}
						},
						name: {
							textStyle: {
								color: '#333',
								fontSize: 14
							}
						}
					},
					series: [
						{
							name: '评分',
							type: 'radar',
							data: [
								{
									value: values,
									name: '评分',
									areaStyle: {
										color: 'rgba(16,185,129,0.4)'
									},
									lineStyle: {
										color: '#10b981'
									},
									itemStyle: {
										color: '#10b981'
									}
								}
							]
						}
					]
				};
				chart.setOption(option);
				return chart;
			},
			scrollToAnalysis(index) {
				this.activeAnalysisIndex = index;
				this.navScrollIntoView = 'nav-item-' + index;
				this.$nextTick(() => {
					uni.pageScrollTo({
						selector: `#analysis-${index}`,
						duration: 300,
						offsetTop: 120
					});
				});
			},
			fetchOrganization(url, data, header) {
				return new Promise((resolve, reject) => {
					uni.request({
						url: this.apiBaseUrl + url,
						method: 'POST',
						data,
						header,
						success: res => {
							if (res.data && res.data.success) resolve(res.data.data);
							else reject(res);
						},
						fail: reject
					});
				});
			},
			fetchPersuasiveness(url, data, header) {
				return new Promise((resolve, reject) => {
					uni.request({
						url: this.apiBaseUrl + url,
						method: 'POST',
						data,
						header,
						success: res => {
							if (res.data && res.data.success) resolve(res.data.data);
							else reject(res);
						},
						fail: reject
					});
				});
			},
			fetchFluencyExpressionPronunciation(url, data, header) {
				return new Promise((resolve, reject) => {
					uni.request({
						url: this.apiBaseUrl + url,
						method: 'POST',
						data,
						header,
						success: res => {
							if (res.data && res.data.success) resolve(res.data.data);
							else reject(res);
						},
						fail: reject
					});
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
						url: `${this.apiBaseUrl}/reports/${reportId}`,
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
								this.$refs.canvas.init(this.initChart);
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
		position: relative;
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
	
	.score-section.vertical {
		display: flex;
		flex-direction: column;
		align-items: center;
		background-color: #fff;
		border-radius: 12rpx;
		padding: 20rpx 10rpx 10rpx 10rpx;
		margin-bottom: 20rpx;
		min-height: 500rpx;
	}
	
	.overall-score {
		text-align: center;
		margin-bottom: 4rpx;
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
		width: 100%;
		height: 500rpx;
		max-width: 700px;
		margin: 0 auto;
		display: flex;
		justify-content: center;
		align-items: center;
	}
	
	.radar-canvas {
		width: 100%;
		height: 500rpx;
		display: block;
	}

	.loading-container {
		display: flex;
		justify-content: center;
		align-items: center;
		height: 500rpx;
		background-color: rgba(255, 255, 255, 0.8);
		border-radius: 12rpx;
	}

	.loading-text {
		font-size: 36rpx;
		color: #10b981;
		font-weight: bold;
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

	/* 横向评分维度导航 */
	.dimension-nav {
		width: 100%;
		display: flex;
		flex-direction: row;
		overflow-x: auto;
		white-space: nowrap;
		margin-bottom: 20rpx;
		padding-bottom: 10rpx;
		border-bottom: 1rpx solid #eee;
		background: #fff;
		-webkit-overflow-scrolling: touch;
		scrollbar-width: none;
	}
	.dimension-nav::-webkit-scrollbar {
		display: none;
	}
	.dimension-nav-item {
		display: inline-block;
		flex-shrink: 0;
		padding: 4rpx 10rpx;
		font-size: 24rpx;
		color: #666;
		border-radius: 18rpx;
		margin-right: 6rpx;
		background: #f5f5f5;
		transition: background 0.2s, color 0.2s;
		white-space: nowrap;
	}
	.dimension-nav-item.active {
		background: #10b981;
		color: #fff;
		font-weight: bold;
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