<template>
  <view class="synthesize-digital-human-container">
    <!-- 顶部标题栏 -->
    <view class="header">
      <view class="header-left" @click="goBack">
        <uni-icons type="left" size="24" color="#fff"></uni-icons>
      </view>
      <text class="title">合成数字人</text>
      <view class="header-right"></view>
    </view>
    
    <!-- 主要内容区域 -->
    <view class="content">
      <!-- 说明文字 -->
      <view class="intro-section">
        <text class="intro-title">合成数字人</text>
        <text class="intro-desc">选择分身和音色，输入文本内容合成数字人视频</text>
      </view>
      
      <!-- 选择分身 -->
      <view class="section">
        <view class="section-header">
          <text class="section-title">选择分身</text>
          <text class="section-required">*</text>
        </view>
        <view class="clone-selector" @click="showCloneSelector">
          <view v-if="selectedClone" class="selected-item">
            <image v-if="selectedClone.cover_url" :src="selectedClone.cover_url" class="selected-image" mode="aspectFill"></image>
            <view v-else class="selected-placeholder">
              <uni-icons type="videocam" size="24" color="#999"></uni-icons>
            </view>
            <view class="selected-info">
              <text class="selected-name">{{ selectedClone.name }}</text>
              <text class="selected-status" :class="selectedClone.status">{{ getStatusText(selectedClone.status) }}</text>
            </view>
          </view>
          <view v-else class="placeholder">
            <uni-icons type="plus" size="24" color="#999"></uni-icons>
            <text class="placeholder-text">选择分身</text>
          </view>
          <uni-icons type="right" size="16" color="#999"></uni-icons>
        </view>
      </view>
      
      <!-- 选择音色 -->
      <view class="section">
        <view class="section-header">
          <text class="section-title">选择音色</text>
          <text class="section-required">*</text>
        </view>
        <view class="voice-selector" @click="showVoiceSelector">
          <view v-if="selectedVoice" class="selected-item">
            <view class="selected-voice-icon">
              <uni-icons type="sound" size="24" color="#FF8E53"></uni-icons>
            </view>
            <view class="selected-info">
              <text class="selected-name">{{ selectedVoice.name }}</text>
              <!-- 已移除试听播放器和按钮，只保留音色名称 -->
            </view>
          </view>
          <view v-else class="placeholder">
            <uni-icons type="plus" size="24" color="#999"></uni-icons>
            <text class="placeholder-text">选择音色</text>
          </view>
          <uni-icons type="right" size="16" color="#999"></uni-icons>
        </view>
      </view>
      
      <!-- 输入文本 -->
      <view class="section">
        <view class="section-header">
          <text class="section-title">合成文本</text>
          <text class="section-required">*</text>
        </view>
        <view class="text-input-container">
          <textarea 
            v-model="synthesisText" 
            class="text-input" 
            placeholder="请输入要合成的文本内容..."
            :maxlength="500"
            auto-height
          ></textarea>
          <text class="text-counter">{{ synthesisText.length }}/500</text>
        </view>
      </view>
      
      <!-- 合成按钮 -->
      <view class="action-section">
        <button 
          class="synthesize-btn" 
          :class="{ 'disabled': !canSynthesize || synthesizing }"
          :disabled="!canSynthesize || synthesizing"
          @click="startSynthesis"
        >
          <text v-if="!synthesizing">开始合成</text>
          <text v-else>合成中...</text>
        </button>
      </view>
      
      <!-- 合成结果 -->
      <view v-if="synthesisResult" class="result-section">
        <view class="section-header">
          <text class="section-title">合成结果</text>
        </view>
        <view class="result-content">
          <view v-if="synthesisResult.status === 'processing'" class="processing">
            <uni-icons type="spinner-cycle" size="32" color="#1AAD19"></uni-icons>
            <text class="processing-text">正在合成中，请稍候...</text>
          </view>
          <view v-else-if="synthesisResult.status === 'completed'" class="completed">
            <video 
              v-if="synthesisResult.video_url" 
              :src="synthesisResult.video_url" 
              class="result-video" 
              controls
              poster="synthesisResult.cover_url"
            ></video>
            <view class="result-info">
              <text class="result-duration" v-if="synthesisResult.duration">时长: {{ formatDuration(synthesisResult.duration) }}</text>
              <text class="result-time">完成时间: {{ formatTime(synthesisResult.update_time) }}</text>
            </view>
          </view>
          <view v-else-if="synthesisResult.status === 'failed'" class="failed">
            <uni-icons type="closeempty" size="32" color="#FF6B6B"></uni-icons>
            <text class="failed-text">合成失败，请重试</text>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 分身选择弹窗 -->
    <!-- 已移除，改为页面跳转 -->
    
    <!-- 音色选择弹窗 -->
    <!-- 已移除，改为页面跳转 -->
  </view>
</template>

<script>
import config from '@/config.js'
import uniIcons from '@dcloudio/uni-ui/lib/uni-icons/uni-icons.vue'

export default {
  components: { uniIcons },
  data() {
    return {
      selectedClone: null,
      selectedVoice: null,
      synthesisText: '',
      synthesizing: false,
      synthesisResult: null,
      statusPollingTimer: null
    };
  },
  computed: {
    canSynthesize() {
      return this.selectedClone && 
             this.selectedClone.status === 'completed' &&
             this.selectedVoice && 
             this.selectedVoice.status === 'completed' &&
             this.synthesisText.trim().length > 0 &&
             !this.synthesizing;
    }
  },
  onLoad() {
    // 页面加载时不需要加载列表，改为页面跳转选择
  },
  onUnload() {
    this.stopStatusPolling();
  },
  methods: {
    goBack() {
      uni.navigateBack();
    },
    
    // 显示分身选择器
    showCloneSelector() {
      uni.navigateTo({
        url: '/pages/select-clone/select-clone'
      });
    },
    
    // 隐藏分身选择器
    hideCloneSelector() {
      // 已移除，不再需要
    },
    
    // 选择分身
    selectClone(clone) {
      this.selectedClone = clone;
      this.hideCloneSelector();
    },
    
    // 显示音色选择器
    showVoiceSelector() {
      uni.navigateTo({
        url: '/pages/select-voice/select-voice'
      });
    },
    
    // 隐藏音色选择器
    hideVoiceSelector() {
      // 已移除，不再需要
    },
    
    // 选择音色
    selectVoice(voice) {
      this.selectedVoice = voice;
      this.hideVoiceSelector();
    },
    
    // 获取状态文本
    getStatusText(status) {
      const statusMap = {
        'processing': '处理中',
        'completed': '已完成',
        'failed': '失败'
      };
      return statusMap[status] || status;
    },
    
    // 开始合成
    async startSynthesis() {
      if (!this.canSynthesize) return;
      
      this.synthesizing = true;
      this.synthesisResult = null;
      
      try {
        const response = await uni.request({
          url: config.apiBaseUrl + '/api/digital-human/synthesize',
          method: 'POST',
          header: {
            'Authorization': `Bearer ${uni.getStorageSync('token')}`,
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          data: {
            scene_task_id: this.selectedClone.scene_task_id,
            voice_id: this.selectedVoice.voice_id,
            text: this.synthesisText.trim()
          }
        });
        
        if (response.data.success) {
          const videoTaskId = response.data.data.video_task_id;
          this.synthesisResult = {
            video_task_id: videoTaskId,
            status: 'processing',
            update_time: new Date().toISOString()
          };
          
          // 开始轮询状态
          this.startStatusPolling(videoTaskId);
          
          uni.showToast({
            title: '合成任务已提交',
            icon: 'success'
          });
        } else {
          throw new Error(response.data.message || '合成失败');
        }
      } catch (error) {
        console.error('合成失败:', error);
        uni.showToast({
          title: error.message || '合成失败',
          icon: 'none'
        });
      } finally {
        this.synthesizing = false;
      }
    },
    
    // 开始状态轮询
    startStatusPolling(videoTaskId) {
      this.stopStatusPolling();
      this.statusPollingTimer = setInterval(async () => {
        try {
          const response = await uni.request({
            url: config.apiBaseUrl + '/api/digital-human/synthesize-status/' + videoTaskId,
            method: 'GET',
            header: {
              'Authorization': `Bearer ${uni.getStorageSync('token')}`
            }
          });
          
          if (response.data.success) {
            const data = response.data.data;
            this.synthesisResult = {
              video_task_id: data.video_task_id,
              status: data.status,
              video_url: data.video_url,
              cover_url: data.cover_url,
              duration: data.duration,
              update_time: data.update_time
            };
            
            // 如果完成或失败，停止轮询
            if (data.status === 'completed' || data.status === 'failed') {
              this.stopStatusPolling();
              
              if (data.status === 'completed') {
                uni.showToast({
                  title: '合成完成',
                  icon: 'success'
                });
              } else {
                uni.showToast({
                  title: '合成失败',
                  icon: 'none'
                });
              }
            }
          }
        } catch (error) {
          console.error('查询状态失败:', error);
        }
      }, 3000); // 每3秒查询一次
    },
    
    // 停止状态轮询
    stopStatusPolling() {
      if (this.statusPollingTimer) {
        clearInterval(this.statusPollingTimer);
        this.statusPollingTimer = null;
      }
    },
    
    // 格式化时长
    formatDuration(duration) {
      if (!duration) return '';
      const minutes = Math.floor(duration / 60);
      const seconds = Math.floor(duration % 60);
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    },
    
    // 格式化时间
    formatTime(timeStr) {
      if (!timeStr) return '';
      const date = new Date(timeStr);
      return date.toLocaleString('zh-CN');
    }
  }
}
</script>

<style>
.synthesize-digital-human-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
}

.header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 40rpx 30rpx 20rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.title {
  font-size: 36rpx;
  font-weight: bold;
  color: #fff;
}

.header-right {
  width: 60rpx;
}

.content {
  padding: 40rpx 30rpx;
}

.intro-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20rpx;
  padding: 40rpx;
  margin-bottom: 40rpx;
  text-align: center;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.1);
}

.intro-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 16rpx;
}

.intro-desc {
  font-size: 26rpx;
  color: #666;
  line-height: 1.5;
}

.section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
}

.section-required {
  color: #FF6B6B;
  margin-left: 8rpx;
}

.clone-selector,
.voice-selector {
  display: flex;
  align-items: center;
  padding: 20rpx;
  border: 2rpx dashed #ddd;
  border-radius: 12rpx;
  background: #f8f9fa;
}

.selected-item {
  display: flex;
  align-items: center;
  flex: 1;
}

.selected-image,
.selected-placeholder,
.selected-voice-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: 12rpx;
  margin-right: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
}

.selected-info {
  flex: 1;
}

.selected-name {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
}

.selected-status {
  font-size: 24rpx;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  display: inline-block;
}

.selected-status.processing {
  background: #FFF3CD;
  color: #856404;
}

.selected-status.completed {
  background: #D4EDDA;
  color: #155724;
}

.selected-status.failed {
  background: #F8D7DA;
  color: #721C24;
}

.placeholder {
  display: flex;
  align-items: center;
  flex: 1;
  color: #999;
}

.placeholder-text {
  font-size: 28rpx;
  margin-left: 16rpx;
}

.text-input-container {
  position: relative;
}

.text-input {
  width: 100%;
  min-height: 200rpx;
  padding: 20rpx;
  border: 2rpx solid #ddd;
  border-radius: 12rpx;
  font-size: 28rpx;
  line-height: 1.5;
  background: #fff;
  box-sizing: border-box;
}

.text-counter {
  position: absolute;
  bottom: 20rpx;
  right: 20rpx;
  font-size: 24rpx;
  color: #999;
}

.action-section {
  margin: 40rpx 0;
}

.synthesize-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #1AAD19 0%, #2ECC71 100%);
  border: none;
  border-radius: 44rpx;
  color: #fff;
  font-size: 32rpx;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(26, 173, 25, 0.3);
  transition: all 0.3s ease;
}

.synthesize-btn.disabled {
  background: #ccc;
  box-shadow: none;
}

.synthesize-btn:active {
  transform: scale(0.98);
}

.result-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20rpx;
  padding: 30rpx;
  margin-top: 40rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
}

.result-content {
  margin-top: 20rpx;
}

.processing,
.completed,
.failed {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx;
}

.processing-text,
.failed-text {
  font-size: 28rpx;
  color: #666;
  margin-top: 20rpx;
}

.result-video {
  width: 100%;
  height: 400rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
}

.result-info {
  text-align: center;
}

.result-duration,
.result-time {
  font-size: 26rpx;
  color: #666;
  display: block;
  margin-bottom: 8rpx;
}

.voice-audio {
  margin-top: 10rpx;
}

/* 弹窗样式 */
/* 已移除，改为页面跳转 */

/* 弹窗样式 */
</style> 