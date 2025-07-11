<template>
  <view class="clone-voice-container">
    <!-- 顶部标题栏 -->
    <view class="header">
      <view class="header-left" @click="goBack">
        <uni-icons type="left" size="24" color="#fff"></uni-icons>
      </view>
      <text class="title">克隆语音</text>
      <view class="header-right"></view>
    </view>
    
    <!-- 主要内容区域 -->
    <view class="content">
      <!-- 说明文字 -->
      <view class="intro-section">
        <text class="intro-title">克隆专属音色</text>
        <text class="intro-desc">上传音频样本，我们将为您克隆专属音色</text>
      </view>
      
      <!-- 上传功能区域 -->
      <view class="upload-section">
        <!-- 上传音频 -->
        <view class="upload-item" @click="chooseAudio">
          <view class="upload-icon">
            <uni-icons type="sound" size="32" color="#FF8E53"></uni-icons>
          </view>
          <view class="upload-content">
            <text class="upload-title">上传音频</text>
            <text class="upload-desc">上传语音样本，用于克隆音色</text>
            <text class="upload-status" v-if="audioFileName">已选音频：{{ audioFileName }}</text>
          </view>
          <view class="upload-arrow">
            <uni-icons type="right" size="16" color="#999"></uni-icons>
          </view>
        </view>
      </view>
      
      <!-- 音色信息输入 -->
      <view class="input-section">
        <view class="input-item">
          <text class="input-label">音色名称</text>
          <input 
            v-model="voiceName" 
            placeholder="请输入音色名称，如：张宇凡的声音" 
            class="input-field"
          />
        </view>
        <view class="input-item">
          <text class="input-label">音色描述（可选）</text>
          <textarea 
            v-model="voiceDescription" 
            placeholder="请输入音色描述，如：磁性男声" 
            class="textarea-field"
          />
        </view>
      </view>
      
      <!-- 开始克隆按钮 -->
      <view class="action-section">
        <button 
          class="clone-btn" 
          @click="startClone" 
          :disabled="!canClone || isCloning"
        >
          <uni-icons type="mic" size="20" color="#fff"></uni-icons>
          <text class="btn-text">{{ isCloning ? '克隆中...' : '开始克隆音色' }}</text>
        </button>
      </view>
      
      <!-- 克隆结果展示 -->
      <view v-if="cloneResult" class="result-section">
        <view class="result-header">
          <uni-icons type="checkmarkempty" size="24" color="#1AAD19"></uni-icons>
          <text class="result-title">克隆成功！</text>
        </view>
        <view class="result-content">
          <text class="result-item">音色ID：{{ cloneResult.voice_id }}</text>
          <text class="result-item">音色名称：{{ cloneResult.name }}</text>
          <text class="result-item">创建时间：{{ cloneResult.create_time }}</text>
        </view>
        <!-- 音频播放器 -->
        <view v-if="audioUrl" class="audio-player">
          <text class="audio-title">原始音频：</text>
          <audio :src="audioUrl" controls style="width: 100%; margin-top: 10rpx;"></audio>
        </view>
      </view>
    </view>
    
    <!-- 录音指示器 -->
    <view v-if="isRecording" class="recording-indicator">
      <view class="recording-dot"></view>
      <text class="recording-text">录音中... {{ recordDuration }}s</text>
      <button class="stop-record-btn" @click="stopRecording" size="mini" type="warn">停止录音</button>
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
      audioUrl: '',           // 上传后的音频URL
      audioFileName: '',      // 上传音频的文件名
      voiceName: '',          // 音色名称
      voiceDescription: '',   // 音色描述
      isCloning: false,       // 是否正在克隆
      cloneResult: null,      // 克隆结果
      isRecording: false,     // 是否正在录音
      recordDuration: 0,      // 录音时长
      recordTimer: null,      // 录音定时器
    }
  },
  computed: {
    canClone() {
      return this.audioUrl && this.voiceName.trim();
    }
  },
  methods: {
    goBack() {
      uni.navigateBack();
    },
    
    // 选择音频
    chooseAudio() {
      // #ifdef H5 || APP-PLUS
      uni.chooseFile({
        count: 1,
        type: 'file',
        extension: ['.mp3', '.wav', '.m4a'],
        success: (res) => {
          const tempFilePath = res.tempFiles[0].path;
          this.audioFileName = tempFilePath.split('/').pop();
          this.uploadAudio(tempFilePath);
        }
      });
      // #endif
      
      // #ifdef MP-WEIXIN
      // 添加微信文件选择功能
      uni.showActionSheet({
        itemList: ['从微信聊天中选择文件', '录音上传'],
        success: (res) => {
          if (res.tapIndex === 0) {
            // 从微信聊天中选择文件
            this.chooseWechatFile();
          } else if (res.tapIndex === 1) {
            // 录音上传
            this.startRecording();
          }
        }
      });
      // #endif
    },
    
    // 从微信聊天中选择文件
    chooseWechatFile() {
      uni.chooseMessageFile({
        count: 1,
        type: 'file',
        extension: ['mp3', 'wav', 'm4a'],
        success: (res) => {
          const tempFilePath = res.tempFiles[0].path;
          this.audioFileName = res.tempFiles[0].name || '微信音频文件.mp3';
          this.uploadAudio(tempFilePath);
        },
        fail: (err) => {
          console.log('选择文件失败:', err);
          uni.showToast({
            title: '选择文件失败',
            icon: 'none'
          });
        }
      });
    },
    
    // 开始录音（小程序）
    startRecording() {
      const recorderManager = uni.getRecorderManager();
      this.isRecording = true;
      this.recordDuration = 0;
      this.recordTimer = setInterval(() => {
        this.recordDuration++;
      }, 1000);
      recorderManager.start({
        format: 'mp3',
        duration: 60000 // 最长60秒
      });
      
      // 添加录音结束回调
      recorderManager.onStop((res) => {
        this.stopRecording();
        this.audioFileName = '录音文件.mp3';
        this.uploadAudio(res.tempFilePath);
      });
    },
    
    // 停止录音（小程序）
    stopRecording() {
      // #ifdef MP-WEIXIN
      const recorderManager = uni.getRecorderManager();
      recorderManager.stop();
      // #endif
      this.isRecording = false;
      if (this.recordTimer) {
        clearInterval(this.recordTimer);
        this.recordTimer = null;
      }
    },
    
    // 上传音频
    uploadAudio(filePath) {
      uni.showLoading({ title: '上传中...' });
      uni.uploadFile({
        url: config.apiBaseUrl + '/api/digital-human/upload-audio',
        filePath: filePath,
        name: 'file',
        header: {
          'Authorization': `Bearer ${uni.getStorageSync('token')}`
        },
        success: (res) => {
          uni.hideLoading();
          const data = JSON.parse(res.data);
          if (data.success) {
            this.audioUrl = data.file_url;
            uni.showToast({ title: '上传成功', icon: 'success' });
          } else {
            uni.showToast({ title: data.message || '上传失败', icon: 'none' });
          }
        },
        fail: () => {
          uni.hideLoading();
          uni.showToast({ title: '上传失败', icon: 'none' });
        }
      });
    },
    
    // 开始克隆
    startClone() {
      if (!this.canClone || this.isCloning) return;
      
      this.isCloning = true;
      uni.showLoading({ title: '克隆中...' });
      
      uni.request({
        url: config.apiBaseUrl + '/api/digital-human/clone-voice',
        method: 'POST',
        header: {
          'Authorization': `Bearer ${uni.getStorageSync('token')}`,
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        data: {
          audio_url: this.audioUrl,
          name: this.voiceName,
          description: this.voiceDescription
        },
        success: (res) => {
          uni.hideLoading();
          this.isCloning = false;
          
          if (res.data.success) {
            this.cloneResult = {
              voice_id: res.data.voice_id,
              name: this.voiceName,
              create_time: new Date().toLocaleString()
            };
            uni.showToast({ title: '克隆成功', icon: 'success' });
          } else {
            uni.showToast({ title: res.data.message || '克隆失败', icon: 'none' });
          }
        },
        fail: () => {
          uni.hideLoading();
          this.isCloning = false;
          uni.showToast({ title: '克隆失败', icon: 'none' });
        }
      });
    }
  },
  beforeDestroy() {
    if (this.recordTimer) {
      clearInterval(this.recordTimer);
    }
  }
}
</script>

<style>
.clone-voice-container {
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

.upload-section {
  margin-bottom: 40rpx;
}

.upload-item {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20rpx;
  padding: 30rpx;
  display: flex;
  align-items: center;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.upload-item:active {
  transform: scale(0.98);
}

.upload-icon {
  width: 80rpx;
  height: 80rpx;
  background: rgba(255, 142, 83, 0.1);
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 30rpx;
}

.upload-content {
  flex: 1;
}

.upload-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
}

.upload-desc {
  font-size: 24rpx;
  color: #666;
  display: block;
  margin-bottom: 8rpx;
}

.upload-status {
  font-size: 22rpx;
  color: #1AAD19;
  display: block;
}

.upload-arrow {
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.input-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 40rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
}

.input-item {
  margin-bottom: 30rpx;
}

.input-item:last-child {
  margin-bottom: 0;
}

.input-label {
  font-size: 28rpx;
  color: #333;
  display: block;
  margin-bottom: 16rpx;
  font-weight: bold;
}

.input-field {
  width: 100%;
  height: 80rpx;
  border: 1rpx solid #ddd;
  border-radius: 10rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.textarea-field {
  width: 100%;
  height: 120rpx;
  border: 1rpx solid #ddd;
  border-radius: 10rpx;
  padding: 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
  resize: none;
}

.action-section {
  margin-bottom: 40rpx;
}

.clone-btn {
  background: linear-gradient(45deg, #FF8E53, #FF6B6B);
  border: none;
  border-radius: 50rpx;
  padding: 30rpx 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(255, 142, 83, 0.3);
  transition: all 0.3s ease;
  width: 100%;
}

.clone-btn:active {
  transform: translateY(2rpx);
  box-shadow: 0 4rpx 12rpx rgba(255, 142, 83, 0.3);
}

.clone-btn[disabled] {
  background: #ccc;
  box-shadow: none;
}

.btn-text {
  color: #fff;
  font-size: 30rpx;
  font-weight: bold;
  margin-left: 10rpx;
}

.result-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
}

.result-header {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}

.result-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #1AAD19;
  margin-left: 10rpx;
}

.result-content {
  margin-bottom: 20rpx;
}

.result-item {
  font-size: 26rpx;
  color: #666;
  display: block;
  margin-bottom: 8rpx;
}

.audio-player {
  border-top: 1rpx solid #eee;
  padding-top: 20rpx;
}

.audio-title {
  font-size: 26rpx;
  color: #333;
  display: block;
  margin-bottom: 10rpx;
}

/* 录音指示器样式 */
.recording-indicator {
  position: fixed;
  top: 30%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 9999;
  background: rgba(0,0,0,0.7);
  border-radius: 20rpx;
  padding: 30rpx 40rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  min-width: 400rpx;
}

.recording-dot {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  background: #ff3b30;
  margin-right: 20rpx;
  animation: blink 1s infinite;
  flex-shrink: 0;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.recording-text {
  color: #fff;
  font-size: 32rpx;
  font-weight: bold;
  flex: 1;
  white-space: nowrap;
}

.stop-record-btn {
  margin-left: 20rpx;
  height: 48rpx;
  line-height: 48rpx;
  padding: 0 24rpx;
  font-size: 26rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
</style> 