<template>
  <view class="select-voice-container">
    <!-- 顶部标题栏 -->
    <view class="header">
      <view class="header-left" @click="goBack">
        <uni-icons type="left" size="24" color="#fff"></uni-icons>
      </view>
      <text class="title">选择音色</text>
      <view class="header-right"></view>
    </view>
    
    <!-- 主要内容区域 -->
    <view class="content">
      <!-- 说明文字 -->
      <view class="intro-section">
        <text class="intro-title">选择音色</text>
        <text class="intro-desc">请选择要用于合成的音色</text>
      </view>
      
      <!-- 音色列表 -->
      <view class="voice-list">
        <view v-if="voiceList.length === 0" class="empty-list">
          <uni-icons type="info" size="64" color="#999"></uni-icons>
          <text class="empty-title">暂无音色</text>
          <text class="empty-desc">请先克隆语音音色</text>
          <button class="create-btn" @click="goToCloneVoice">去克隆音色</button>
        </view>
        
        <view v-else>
          <view 
            v-for="voice in voiceList" 
            :key="voice.voice_id"
            class="voice-item"
            :class="{ 'selected': selectedVoice && selectedVoice.voice_id === voice.voice_id }"
            @click="selectVoice(voice)"
          >
            <!-- 音色图标 -->
            <view class="voice-icon">
              <uni-icons type="sound" size="32" color="#FF8E53"></uni-icons>
            </view>
            
            <!-- 音色信息 -->
            <view class="voice-info">
              <text class="voice-name">{{ voice.name }}</text>
              <text class="voice-time">创建时间: {{ formatTime(voice.create_time) }}</text>
              
              <!-- 状态标签 -->
              <view class="status-badge" :class="voice.status">
                {{ getStatusText(voice.status) }}
              </view>
            </view>
            
            <!-- 音频播放器 -->
            <view v-if="voice.audio_url" class="audio-player">
              <button class="play-btn" @click.stop="playAudio(voice.audio_url)">
                <uni-icons :type="isPlaying && currentAudio === voice.audio_url ? 'pause' : 'play'" size="20" color="#1AAD19"></uni-icons>
              </button>
            </view>
            
            <!-- 选择指示器 -->
            <view v-if="selectedVoice && selectedVoice.voice_id === voice.voice_id" class="select-indicator">
              <uni-icons type="checkmarkempty" size="24" color="#1AAD19"></uni-icons>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 确认按钮 -->
      <view v-if="voiceList.length > 0" class="action-section">
        <button 
          class="confirm-btn" 
          :class="{ 'disabled': !selectedVoice }"
          :disabled="!selectedVoice"
          @click="confirmSelection"
        >
          确认选择
        </button>
      </view>
    </view>
  </view>
</template>

<script>
import config from '@/config.js'
import uniIcons from '@dcloudio/uni-ui/lib/uni-icons/uni-icons.vue'

export default {
  components: { uniIcons },
  data() {
    return {
      voiceList: [],
      selectedVoice: null,
      isPlaying: false,
      currentAudio: null
    };
  },
  onLoad() {
    this.loadVoiceList();
  },
  methods: {
    goBack() {
      uni.navigateBack();
    },
    
    // 加载音色列表
    async loadVoiceList() {
      try {
        uni.showLoading({ title: '加载中...' });
        
        const response = await uni.request({
          url: config.apiBaseUrl + '/api/digital-human/voices',
          method: 'GET',
          header: {
            'Authorization': `Bearer ${uni.getStorageSync('token')}`
          }
        });
        
        uni.hideLoading();
        
        if (response.data.success) {
          this.voiceList = response.data.data;
        } else {
          uni.showToast({
            title: response.data.message || '加载失败',
            icon: 'none'
          });
        }
      } catch (error) {
        uni.hideLoading();
        console.error('加载音色列表失败:', error);
        uni.showToast({
          title: '加载音色列表失败',
          icon: 'none'
        });
      }
    },
    
    // 选择音色
    selectVoice(voice) {
      if (voice.status !== 'completed') {
        uni.showToast({
          title: '只能选择已完成的音色',
          icon: 'none'
        });
        return;
      }
      this.selectedVoice = voice;
    },
    
    // 播放音频
    playAudio(audioUrl) {
      if (this.isPlaying && this.currentAudio === audioUrl) {
        // 停止播放
        uni.stopBackgroundAudio();
        this.isPlaying = false;
        this.currentAudio = null;
      } else {
        // 开始播放
        if (this.currentAudio) {
          uni.stopBackgroundAudio();
        }
        
        uni.playBackgroundAudio({
          dataUrl: audioUrl,
          title: '音色试听',
          success: () => {
            this.isPlaying = true;
            this.currentAudio = audioUrl;
          },
          fail: () => {
            uni.showToast({
              title: '播放失败',
              icon: 'none'
            });
          }
        });
      }
    },
    
    // 确认选择
    confirmSelection() {
      if (!this.selectedVoice) return;
      
      // 停止音频播放
      if (this.isPlaying) {
        uni.stopBackgroundAudio();
      }
      
      // 返回上一页并传递选中的音色
      const pages = getCurrentPages();
      const prevPage = pages[pages.length - 2];
      
      if (prevPage && prevPage.$vm) {
        prevPage.$vm.selectedVoice = this.selectedVoice;
      }
      
      uni.navigateBack();
    },
    
    // 跳转到克隆音色页面
    goToCloneVoice() {
      uni.navigateTo({
        url: '/pages/clone-voice/clone-voice'
      });
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
    
    // 格式化时间
    formatTime(timeStr) {
      if (!timeStr) return '';
      const date = new Date(timeStr);
      return date.toLocaleDateString('zh-CN');
    }
  },
  
  // 页面卸载时停止音频播放
  onUnload() {
    if (this.isPlaying) {
      uni.stopBackgroundAudio();
    }
  }
}
</script>

<style>
.select-voice-container {
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

.voice-list {
  margin-bottom: 40rpx;
}

.empty-list {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20rpx;
  padding: 80rpx 40rpx;
  text-align: center;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
}

.empty-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin: 20rpx 0 10rpx;
}

.empty-desc {
  font-size: 26rpx;
  color: #666;
  display: block;
  margin-bottom: 40rpx;
}

.create-btn {
  background: linear-gradient(135deg, #FF8E53 0%, #FF6B6B 100%);
  color: #fff;
  border: none;
  border-radius: 44rpx;
  padding: 20rpx 40rpx;
  font-size: 28rpx;
  font-weight: bold;
}

.voice-item {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  position: relative;
}

.voice-item.selected {
  border: 3rpx solid #FF8E53;
  background: rgba(255, 142, 83, 0.05);
}

.voice-item:active {
  transform: scale(0.98);
}

.voice-icon {
  width: 80rpx;
  height: 80rpx;
  background: rgba(255, 142, 83, 0.1);
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 30rpx;
}

.voice-info {
  flex: 1;
  position: relative;
}

.voice-name {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 12rpx;
}

.voice-time {
  font-size: 24rpx;
  color: #666;
  display: block;
  margin-bottom: 8rpx;
}

.status-badge {
  display: inline-block;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  font-size: 20rpx;
  font-weight: bold;
}

.status-badge.processing {
  background: #FFF3CD;
  color: #856404;
}

.status-badge.completed {
  background: #D4EDDA;
  color: #155724;
}

.status-badge.failed {
  background: #F8D7DA;
  color: #721C24;
}

.audio-player {
  margin-right: 20rpx;
}

.play-btn {
  width: 60rpx;
  height: 60rpx;
  background: rgba(26, 173, 25, 0.1);
  border: none;
  border-radius: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.select-indicator {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 142, 83, 0.1);
  border-radius: 30rpx;
}

.action-section {
  margin-top: 40rpx;
}

.confirm-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #FF8E53 0%, #FF6B6B 100%);
  border: none;
  border-radius: 44rpx;
  color: #fff;
  font-size: 32rpx;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(255, 142, 83, 0.3);
  transition: all 0.3s ease;
}

.confirm-btn.disabled {
  background: #ccc;
  box-shadow: none;
}

.confirm-btn:active {
  transform: scale(0.98);
}
</style> 