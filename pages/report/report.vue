<template>
	<view class="container">
		<!-- 顶部导航栏 -->
		<view class="nav-header">
			<view class="nav-tabs">
				<view 
					class="nav-tab" 
					:class="{ active: activeTab === 'report' }"
					@click="switchTab('report')"
				>
					报告
				</view>
				<view 
					class="nav-tab" 
					:class="{ active: activeTab === 'dialogue' }"
					@click="switchTab('dialogue')"
				>
					对话
				</view>
			</view>
		</view>

		<!-- 报告内容 -->
		<view v-if="activeTab === 'report'" class="report-content">
			<view class="report-header">
				<text class="report-title">练习报告</text>
				<text class="scene-name">{{sceneName}}</text>
			</view>
			
			<view class="report-body">
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
			</view>
		</view>

		<!-- 对话记录内容 -->
		<view v-if="activeTab === 'dialogue'" class="dialogue-content">
			<view class="dialogue-header">
				<text class="dialogue-title">对话记录</text>
				<text class="scene-name">{{sceneName}}</text>
			</view>
			
			<!-- 聊天消息区域 -->
			<scroll-view class="chat-messages" :scroll-y="true" :scroll-into-view="'msg-' + chatMessages.length" :scroll-with-animation="true" ref="chatScroll">
				<!-- 加载状态 -->
				<view v-if="chatMessages.length === 0" class="loading-state">
					<text class="loading-text">加载对话记录中...</text>
				</view>
				
				<view v-for="(msg, index) in chatMessages" :key="index" :id="'msg-' + (index + 1)" class="message-item" :class="{ 'robot': msg.from === 'robot', 'user': msg.from === 'user' }">
					<view class="message-avatar">
						<image :src="msg.from === 'customer' || msg.from === 'robot' ? `${apiBaseUrl}/uploads/static/robot-avatar.png` : `${apiBaseUrl}/uploads/static/user-avatar.png`"></image>
					</view>
					<view class="message-content">  
						<!-- 语音消息部分 -->
						<view class="voice-message-container" v-if="msg.voiceUrl">
							<view class="voice-message" :class="{ 'playing': msg.isPlaying }" :style="{ width: calculateVoiceWidth(msg.duration || 3) }" @click="playVoice(msg.voiceUrl, index)">
								<view class="voice-icon" :class="{ 'playing': msg.isPlaying }">
									<span></span>
								</view>
								<view class="voice-duration">{{msg.duration || 3}}''</view>
							</view>
						</view>
						
						<!-- 文字内容部分 -->
						<view class="text-content-container">
							<!-- 文字转录 -->
							<view class="text-transcript">
								<text>{{msg.text}}</text>
							</view>
							
							<!-- 改进建议（仅用户消息显示） -->
							<view v-if="msg.from === 'user' && msg.suggestion" class="suggestion-wrapper">
								<view class="suggestion-btn" @click="toggleSuggestion(index)">
									<text>{{msg.showSuggestion ? '收起表达建议' : '查看表达建议'}}</text>
								</view>
								<view class="suggestion-content" v-if="msg.showSuggestion">
									<view class="suggestion-title">表达建议</view>
									<text class="suggestion-text">{{msg.suggestion}}</text>
								</view>
							</view>
						</view>
					</view>
				</view>
			</scroll-view>
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
				fromChat: false, // 是否来自聊天页面
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
				loading: false,
				activeTab: 'report', // 新增：控制当前显示的tab
				chatMessages: [], // 新增：存储对话消息
				// 语音条宽度配置
				minVoiceWidth: 120, // 最小宽度（rpx）
				maxVoiceWidth: 400, // 最大宽度（rpx）
			}
		},
        onLoad(options) {
			const { practiceId, conversationId, sceneId, fromChat, generateNew } = options;
			this.practiceId = practiceId;
			this.conversationId = conversationId || 'default-conversation-id'; // 添加默认值
			this.sceneId = parseInt(sceneId) || 0;
			this.fromChat = fromChat === 'true'; // 是否来自聊天页面
			this.generateNew = generateNew === 'true'; // 是否强制重新生成
			
			// 添加调试信息
			console.log('report.vue onLoad options:', options);
			console.log('conversationId:', this.conversationId);
			console.log('practiceId:', this.practiceId);
			console.log('fromChat:', this.fromChat);
			console.log('generateNew:', this.generateNew);
			
			// 获取场景名称
			this.getSceneName();
			
			// 根据来源决定是获取已有报告还是重新生成
			if (this.fromChat || this.generateNew) {
				// 来自聊天页面或强制重新生成，重新生成报告
				this.generateNewReport(practiceId);
			} else {
				// 来自练习历史，尝试从数据库获取已有报告
				this.loadExistingReport(practiceId);
			}
		},
		onShow() {
			console.log('页面显示，fromChat:', this.fromChat);
		},
		onHide() {
			console.log('页面隐藏，fromChat:', this.fromChat);
		},
		onBackPress() {
			if (this.fromChat) {
				// 从聊天页面进入，点击返回箭头直接跳转到首页
				uni.reLaunch({
					url: '/pages/index/index'
				});
				return true; // 阻止默认返回行为
			}
			return false; // 使用默认返回行为
		},
		onUnload() {
			console.log('页面卸载，fromChat:', this.fromChat);
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
			loadExistingReport(practiceId) {
				const token = uni.getStorageSync('token');
				const header = {
					'Authorization': `Bearer ${token}`,
					'Content-Type': 'application/json'
				};
				
				uni.request({
					url: this.apiBaseUrl + `/api/report/get-report/${practiceId}`,
					method: 'GET',
					header,
					success: (res) => {
						if (res.data && res.data.success) {
							// 从数据库获取到报告数据
							const reportData = res.data.data;
							this.processReportData(reportData);
							
							// 获取对话记录
							this.loadChatHistory(practiceId, header);
							
							// 显示雷达图
							this.$nextTick(() => {
								if (this.$refs.canvas) {
									this.$refs.canvas.init(this.initChart);
								}
							});
						} else {
							// 没有已有报告，重新生成
							this.generateNewReport(practiceId);
						}
					},
					fail: (err) => {
						console.error('获取已有报告失败:', err);
						// 获取失败，重新生成
						this.generateNewReport(practiceId);
					}
				});
			},
			
			processReportData(reportData) {
				console.log('从数据库获取的报告数据:', reportData);
				const scores = reportData.scores || {};
				console.log('分数数据:', scores);
				
				// 安全获取分数，避免undefined错误
				const getScore = (key) => {
					const scoreData = scores[key];
					return scoreData && scoreData.score ? scoreData.score : 0;
				};
				
				const getAnalysis = (key) => {
					const scoreData = scores[key];
					return scoreData && scoreData.analysis ? scoreData.analysis : '';
				};
				
				// 计算总分
				const scoreValues = [
					getScore('organization'),
					getScore('persuasiveness'),
					getScore('fluency'),
					getScore('pronunciation'),
					getScore('expression')
				];
				const overall = Math.round(scoreValues.reduce((a, b) => a + b, 0) / scoreValues.length);
				
				// 组装维度数据
				const dimensions = [
					{ name: '语言组织能力', score: getScore('organization') },
					{ name: '说服力', score: getScore('persuasiveness') },
					{ name: '流利度', score: getScore('fluency') },
					{ name: '发音准确度', score: getScore('pronunciation') },
					{ name: '语音表达', score: getScore('expression') }
				];
				
				// 组装分析数据
				const analysis = [
					{ title: '语言组织能力', score: getScore('organization'), content: getAnalysis('organization') },
					{ title: '说服力', score: getScore('persuasiveness'), content: getAnalysis('persuasiveness') },
					{ title: '流利度', score: getScore('fluency'), content: getAnalysis('fluency') },
					{ title: '发音准确度', score: getScore('pronunciation'), content: getAnalysis('pronunciation') },
					{ title: '语音表达', score: getScore('expression'), content: getAnalysis('expression') }
				];
				
				const suggestions = [
					getAnalysis('organization'),
					getAnalysis('persuasiveness'),
					getAnalysis('fluency'),
					getAnalysis('pronunciation'),
					getAnalysis('expression')
				];
				
				console.log('处理后的报告数据:', { overall, dimensions, analysis });
				this.report = { overall, dimensions, analysis, suggestions };
			},
			
			generateNewReport(practiceId) {
				// 原来的重新生成报告逻辑
				this.loading = true;
				uni.showLoading({ title: '音频合并中...' });
				
				const token = uni.getStorageSync('token');
				const header = {
					'Authorization': `Bearer ${token}`,
					'Content-Type': 'application/json'
				};

				// 1. 先调用音频合并接口
				uni.request({
					url: this.apiBaseUrl + '/api/report/combine-audio',
					method: 'POST',
					data: { practice_id: practiceId, conversationId: this.conversationId },
					header,
					success: (res) => {
						if (res.data && res.data.success) {
							// 合并成功，拿到 file_path
							const filePath = res.data.data.file_path;
							uni.hideLoading();
							
							// 2. 并发调用两个分析接口
							uni.showLoading({ title: '分析中...' });
							Promise.all([
								this.fetchOrganization('/api/report/analyze-organization', { practice_id: practiceId, conversationId: this.conversationId, output_path: filePath }, header),
								this.fetchPersuasiveness('/api/report/analyze-persuasiveness', { practice_id: practiceId, conversationId: this.conversationId, output_path: filePath }, header),
								this.fetchFluencyExpressionPronunciation('/api/report/analyze-fluency-expression-pronunciation', { practice_id: practiceId, conversationId: this.conversationId, output_path: filePath }, header)
							]).then(([org, pers, fluExpPron]) => {
								console.log('API返回数据:', { org, pers, fluExpPron });
								
								// 组装数据 - 修复数据结构处理
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
								
								// 获取对话记录
								this.loadChatHistory(practiceId, header);
								
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
			loadChatHistory(practiceId, header) {
				// 获取对话记录
				uni.request({
					url: this.apiBaseUrl + '/api/report/get-chat-history',
					method: 'POST',
					data: { practice_id: practiceId },
					header,
					success: (res) => {
						if (res.data && res.data.success) {
							// 处理对话记录数据
							const chatHistory = res.data.data || [];
							this.chatMessages = chatHistory.map(msg => ({
								...msg,
								showSuggestion: false, // 默认不显示建议
								isPlaying: false // 默认不播放
							}));
						} else {
							console.error('获取对话记录失败:', res);
						}
					},
					fail: (err) => {
						console.error('获取对话记录失败:', err);
					}
				});
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
			},
			switchTab(tab) {
				this.activeTab = tab;
				this.activeAnalysisIndex = 0; // 切换tab时重置分析索引
				this.navScrollIntoView = '';
			},
			calculateVoiceWidth(duration) {
				// 将时长转换为数字
				const durationNum = parseInt(duration) || 0;
				
				// 根据时长计算宽度，时长越长宽度越大
				// 这里使用一个简单的线性映射，可以根据需要调整
				let width = this.minVoiceWidth + (durationNum / 60) * (this.maxVoiceWidth - this.minVoiceWidth);
				
				// 确保宽度在最小和最大值之间
				width = Math.max(this.minVoiceWidth, Math.min(width, this.maxVoiceWidth));
				
				return width + 'rpx';
			},
			playVoice(url, index) {
				console.log('播放语音:', url);
				
				// 检查URL是否有效
				if (!url) {
					uni.showToast({
						title: '无效的语音文件',
						icon: 'none'
					});
					return;
				}
				
				const msg = this.chatMessages[index];
				
				// 如果点击的是当前正在播放的语音，则停止播放
				if (msg.isPlaying) {
					msg.isPlaying = false;
					this.$set(this.chatMessages, index, msg);
					return;
				}
				
				// 停止其他正在播放的语音
				this.chatMessages.forEach((item, idx) => {
					if (idx !== index && item.isPlaying) {
						item.isPlaying = false;
						this.$set(this.chatMessages, idx, item);
					}
				});
				
				// 设置当前消息为播放状态
				msg.isPlaying = true;
				this.$set(this.chatMessages, index, msg);
				
				// 创建音频上下文
				const audioContext = uni.createInnerAudioContext();
				
				// 设置音频源
				if (url.startsWith('http')) {
					// 如果是网络URL，先下载到本地再播放
					console.log('下载并播放网络音频:', url);
					
					uni.downloadFile({
						url: url,
						success: (res) => {
							console.log('音频下载成功:', res);
							if (res.statusCode === 200) {
								audioContext.src = res.tempFilePath;
								this.startAudioPlayback(audioContext, msg, index);
							} else {
								console.error('下载失败，状态码:', res.statusCode);
								msg.isPlaying = false;
								this.$set(this.chatMessages, index, msg);
							}
						},
						fail: (err) => {
							console.error('下载失败:', err);
							msg.isPlaying = false;
							this.$set(this.chatMessages, index, msg);
						}
					});
				} else {
					// 如果是本地文件
					audioContext.src = url;
					this.startAudioPlayback(audioContext, msg, index);
				}
			},
			
			startAudioPlayback(audioContext, msg, index) {
				// 监听播放开始
				audioContext.onPlay(() => {
					console.log('开始播放');
				});
				
				// 监听播放错误
				audioContext.onError((err) => {
					console.error('播放错误:', err);
					msg.isPlaying = false;
					this.$set(this.chatMessages, index, msg);
					
					// 释放资源
					try {
						audioContext.destroy();
					} catch (e) {
						console.error('销毁音频上下文失败:', e);
					}
				});
				
				// 监听播放结束
				audioContext.onEnded(() => {
					console.log('播放结束');
					msg.isPlaying = false;
					this.$set(this.chatMessages, index, msg);
					
					// 释放资源
					try {
						audioContext.destroy();
					} catch (e) {
						console.error('销毁音频上下文失败:', e);
					}
				});
				
				// 开始播放
				try {
					audioContext.play();
				} catch (e) {
					console.error('播放音频失败:', e);
					msg.isPlaying = false;
					this.$set(this.chatMessages, index, msg);
				}
			},
			toggleSuggestion(index) {
				const msg = this.chatMessages[index];
				msg.showSuggestion = !msg.showSuggestion;
				this.$set(this.chatMessages, index, msg);
			},
			getSceneName() {
				// 获取场景名称
				const sceneNames = {
					0: '核苷酸介绍',
					1: '新客户开发',
					2: '异议处理',
					3: '产品推荐',
					4: '成交技巧'
				};
				this.sceneName = sceneNames[this.sceneId] || '未知场景';
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
	
	.nav-header {
		background-color: #fff;
		padding: 20rpx 0;
		margin-bottom: 20rpx;
		border-radius: 12rpx;
		box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
	}
	
	.nav-tabs {
		display: flex;
		justify-content: space-around;
		padding: 0 20rpx;
	}

	.nav-tab {
		padding: 10rpx 20rpx;
		font-size: 32rpx;
		font-weight: bold;
		color: #666;
		border-bottom: 4rpx solid transparent;
		transition: all 0.3s ease;
	}

	.nav-tab.active {
		color: #10b981;
		border-bottom-color: #10b981;
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

	.report-body {
		background-color: #fff;
		border-radius: 12rpx;
		padding: 30rpx;
		margin-bottom: 20rpx;
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

	.dialogue-content {
		background-color: #fff;
		border-radius: 12rpx;
		padding: 30rpx;
		margin-bottom: 20rpx;
		min-height: 500rpx; /* 确保内容区域有最小高度 */
	}

	.dialogue-header {
		text-align: center;
		margin-bottom: 20rpx;
	}

	.dialogue-title {
		font-size: 36rpx;
		font-weight: bold;
		color: #333;
		margin-bottom: 10rpx;
	}

	.chat-messages {
		height: 100%; /* 确保scroll-view高度为内容区域 */
		overflow-y: auto; /* 允许垂直滚动 */
		padding-bottom: 20rpx; /* 留出底部空间 */
	}

	.loading-state {
		display: flex;
		justify-content: center;
		align-items: center;
		height: 500rpx; /* 与chat-messages高度一致 */
		background-color: rgba(255, 255, 255, 0.8);
		border-radius: 12rpx;
	}

	.loading-text {
		font-size: 36rpx;
		color: #10b981;
		font-weight: bold;
	}

	.message-item {
		display: flex;
		align-items: flex-start;
		margin-bottom: 30rpx;
		padding: 15rpx 0;
	}

	.message-item.user {
		flex-direction: row-reverse;
	}

	.message-item.robot {
		flex-direction: row;
	}

	.message-item.user .message-avatar {
		margin-right: 0;
		margin-left: 20rpx;
	}

	.message-avatar {
		width: 80rpx;
		height: 80rpx;
		border-radius: 40rpx;
		overflow: hidden;
		margin-right: 20rpx;
		flex-shrink: 0;
		box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
	}

	.message-avatar image {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.message-content {
		max-width: 70%;
		display: flex;
		flex-direction: column;
	}

	.voice-message-container {
		margin-bottom: 15rpx;
	}

	.robot .voice-message-container {
		align-self: flex-start;
	}

	.user .voice-message-container {
		align-self: flex-end;
	}

	.voice-message {
		display: flex;
		align-items: center;
		padding: 15rpx 20rpx;
		border-radius: 8rpx;
		background-color: #fff;
		width: fit-content;
		min-width: 120rpx;
		transition: width 0.3s ease;
		position: relative;
		cursor: pointer;
		box-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.1);
	}

	.voice-message:hover {
		background-color: #e0e0e0;
	}

	.voice-message.playing {
		background-color: #e8f5e8;
		border: 2rpx solid #10b981;
	}

	.voice-icon {
		width: 40rpx;
		height: 40rpx;
		margin-right: 10rpx;
		position: relative;
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-shrink: 0;
	}

	.voice-icon::before,
	.voice-icon::after,
	.voice-icon span {
		content: '';
		width: 4rpx;
		height: 16rpx;
		background: #666;
		border-radius: 4rpx 4rpx 0 0;
		transform-origin: bottom;
	}

	.voice-icon.playing::before,
	.voice-icon.playing::after,
	.voice-icon.playing span {
		animation: voice-wave 1.5s ease-in-out infinite;
	}

	.voice-icon.playing::before {
		animation-delay: 0s;
	}

	.voice-icon.playing span {
		animation-delay: 0.2s;
	}

	.voice-icon.playing::after {
		animation-delay: 0.4s;
	}

	@keyframes voice-wave {
		0%, 100% {
			transform: scaleY(1);
		}
		50% {
			transform: scaleY(1.5);
		}
	}

	.robot .voice-icon {
		filter: brightness(0) saturate(100%) invert(40%) sepia(82%) saturate(1644%) hue-rotate(199deg) brightness(97%) contrast(101%);
	}

	.robot .voice-icon.playing {
		animation: voice-wave 1.5s ease-in-out infinite;
		transform-origin: center;
	}

	.user .voice-message {
		flex-direction: row-reverse;
		background-color: #95EC69;
	}

	.user .voice-icon {
		margin-right: 0;
		margin-left: 10rpx;
	}

	.user .voice-duration {
		margin-right: 10rpx;
		color: #666;
	}

	.robot .voice-duration {
		color: #666;
	}

	.voice-duration {
		font-size: 24rpx;
		color: #666;
		margin-left: 10rpx;
	}

	.text-content-container {
		background-color: #fff;
		border-radius: 12rpx;
		padding: 15rpx;
		box-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.1);
	}

	.robot .text-content-container {
		background-color: #fff;
		color: #333;
	}

	.text-transcript {
		font-size: 28rpx;
		line-height: 1.4;
	}

	.robot .text-transcript {
		color: #333;
	}

	.suggestion-wrapper {
		margin-top: 15rpx;
		border-top: 1rpx dashed #ddd;
		padding-top: 15rpx;
	}

	.robot .suggestion-wrapper {
		border-top: 1rpx dashed rgba(255, 255, 255, 0.3);
	}

	.suggestion-btn {
		display: inline-block;
		font-size: 24rpx;
		color: #007AFF;
		background-color: rgba(0, 122, 255, 0.1);
		padding: 6rpx 15rpx;
		border-radius: 20rpx;
	}

	.robot .suggestion-btn {
		color: #fff;
		background-color: rgba(255, 255, 255, 0.2);
	}

	.suggestion-content {
		margin-top: 10rpx;
		padding: 15rpx;
		background-color: #f9f9f9;
		border-radius: 8rpx;
		border-left: 6rpx solid #007AFF;
	}

	.robot .suggestion-content {
		background-color: rgba(255, 255, 255, 0.1);
		border-left: 6rpx solid #fff;
	}

	.suggestion-title {
		font-size: 24rpx;
		color: #007AFF;
		font-weight: bold;
		margin-bottom: 6rpx;
	}

	.robot .suggestion-title {
		color: #fff;
	}

	.suggestion-text {
		font-size: 26rpx;
		color: #666;
	}

	.robot .suggestion-text {
		color: rgba(255, 255, 255, 0.9);
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