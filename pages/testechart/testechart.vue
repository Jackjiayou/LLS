<template>
	<view>
		<uni-ec-canvas class="uni-ec-canvas" id="uni-ec-canvas" ref="canvas" canvas-id="uni-ec-canvas" :ec="ec">
		</uni-ec-canvas>
	</view>
</template>
 
<script>
	import uniEcCanvas from '@/uni_modules/uni-ec-canvas/uni-ec-canvas.vue'
	import * as echarts from '@/uni_modules/uni-ec-canvas/echarts' 
	let chart = null
	export default {
		components: {
			uniEcCanvas
		},
		props: {
			abnormal: {
				type: Number,
				// 定义是否必须传
				required: true,
				// 定义默认值
				default: 0
			},
			absence: {
				type: Number,
				// 定义是否必须传
				required: true,
				// 定义默认值
				default: 0
			},
		},
		data() {
			return {
				ec: {
					//是否懒加载
					lazyLoad: true
				},
                conversationId: '', // 对话ID
                option : {
                  title: {
                    text: 'Basic Radar Chart'
                  },
                  legend: {
                    data: ['Allocated Budget', 'Actual Spending']
                  },
                  radar: {
                    // shape: 'circle',
                    indicator: [
                      { name: 'Sales', max: 6500 },
                      { name: 'Administration', max: 16000 },
                      { name: 'Information Technology', max: 30000 },
                      { name: 'Customer Support', max: 38000 },
                      { name: 'Development', max: 52000 },
                      { name: 'Marketing', max: 25000 }
                    ]
                  },
                  series: [
                    {
                      name: 'Budget vs spending',
                      type: 'radar',
                      data: [
                        {
                          value: [4200, 3000, 20000, 35000, 50000, 18000],
                          name: 'Allocated Budget'
                        },
                        {
                          value: [5000, 14000, 28000, 26000, 42000, 21000],
                          name: 'Actual Spending'
                        }
                      ]
                    }
                  ]
                }
                
			}
		},
		methods: {
			initChart(canvas, width, height, canvasDpr) {
				chart = echarts.init(canvas, null, {
					width: width, 
					height: height,
					devicePixelRatio: canvasDpr
				})
				canvas.setChart(chart)
				// 使用ECharts官网雷达图option
				const option = {
					title: {
						text: 'Basic Radar Chart'
					},
					legend: {
						data: ['Allocated Budget', 'Actual Spending'] 
					},
					radar: {
						// shape: 'circle',
						indicator: [
							{ name: 'Sales', max: 6500 },
							{ name: 'Administration', max: 16000 },
							{ name: 'Information Technology', max: 30000 },
							{ name: 'Customer Support', max: 38000 },
							{ name: 'Development', max: 52000 },
							{ name: 'Marketing', max: 25000 }
						]
					},
					series: [
						{
							name: 'Budget vs spending',
							type: 'radar',
							data: [
								{
									value: [4200, 3000, 20000, 35000, 50000, 18000],
									name: 'Allocated Budget'
								},
								{
									value: [5000, 14000, 28000, 26000, 42000, 21000],
									name: 'Actual Spending'
								}
							]
						}
					]
				}
				chart.setOption(option)
				return chart
			},
		},
		mounted() {
			this.$refs.canvas.init(this.initChart)
		}
	}
</script>
<style>
	.uni-ec-canvas {
		width: 100%;
		height: 500rpx;
		display: block;
		margin-top: 30rpx;
	}
</style>
 