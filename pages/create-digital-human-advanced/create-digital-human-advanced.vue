<template>
  <view class="create-digital-human-advanced-container">
    <!-- 顶部标题栏 -->
    <view class="header">
      <view class="header-left" @click="goBack">
        <uni-icons type="left" size="24" color="#fff"></uni-icons>
      </view>
      <text class="title">制作数字人</text>
      <view class="header-right"></view>
    </view>
    
    <!-- 主要内容区域 -->
    <view class="content">
      <!-- 说明文字 -->
      <view class="intro-section">
        <text class="intro-title">选择制作方式</text>
        <text class="intro-desc">请选择您想要制作的数字人类型</text>
      </view>
      
      <!-- 功能按钮区域 -->
      <view class="function-section">
        <!-- 克隆数字人 -->
        <view class="function-item" @click="goToCloneHuman">
          <view class="function-icon">
            <uni-icons type="videocam" size="32" color="#FF6B6B"></uni-icons>
          </view>
          <view class="function-content">
            <text class="function-title">克隆数字人</text>
            <text class="function-desc">上传视频克隆分身</text>
          </view>
          <view class="function-arrow">
            <uni-icons type="right" size="16" color="#999"></uni-icons>
          </view>
        </view>
        
        <!-- 克隆语音 -->
        <view class="function-item" @click="goToCloneVoice">
          <view class="function-icon">
            <uni-icons type="sound" size="32" color="#FF8E53"></uni-icons>
          </view>
          <view class="function-content">
            <text class="function-title">克隆语音</text>
            <text class="function-desc">上传音频克隆音色</text>
          </view>
          <view class="function-arrow">
            <uni-icons type="right" size="16" color="#999"></uni-icons>
          </view>
        </view>
        
        <!-- 合成数字人 -->
        <view class="function-item" @click="goToSynthesize">
          <view class="function-icon">
            <uni-icons type="gear" size="32" color="#1AAD19"></uni-icons>
          </view>
          <view class="function-content">
            <text class="function-title">合成数字人</text>
            <text class="function-desc">选择分身和音色合成</text>
          </view>
          <view class="function-arrow">
            <uni-icons type="right" size="16" color="#999"></uni-icons>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import uniIcons from '@dcloudio/uni-ui/lib/uni-icons/uni-icons.vue'

export default {
  components: { uniIcons },
  data() {
    return {
      
    };
  },
  methods: {
    goBack() {
      uni.navigateBack();
    },
    goToCloneHuman() {
      uni.navigateTo({
        url: '/pages/clone-digital-human/clone-digital-human'
      });
    },
    goToCloneVoice() {
      uni.navigateTo({
        url: '/pages/clone-voice/clone-voice'
      });
    },
    goToSynthesize() {
      uni.navigateTo({
        url: '/pages/synthesize-digital-human/synthesize-digital-human'
      });
    }
  }
}
</script>

<style>
.create-digital-human-advanced-container {
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

.function-section {
  margin-bottom: 40rpx;
}

.function-item {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.function-item:active {
  transform: scale(0.98);
}

.function-icon {
  width: 80rpx;
  height: 80rpx;
  background: rgba(26, 173, 25, 0.1);
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 30rpx;
}

.function-content {
  flex: 1;
}

.function-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
}

.function-desc {
  font-size: 24rpx;
  color: #666;
  display: block;
}

.function-arrow {
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style> 