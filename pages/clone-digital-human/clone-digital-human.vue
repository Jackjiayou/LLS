<template>
  <view class="clone-digital-human-container">
    <view class="form-section">
      <button @click="chooseVideo">上传分身视频</button>
      <view v-if="videoFileName">已选视频：{{ videoFileName }}</view>
      <input v-model="name" placeholder="请输入分身名称" />
      <button :disabled="!videoUrl || !name || isCloning" @click="startClone">开始克隆数字人</button>
    </view>
    <view v-if="isCloning">
      <text>克隆中，请稍候...</text>
    </view>
    <view v-if="cloneStatus === 'completed'">
      <text>克隆完成！</text>
      <video :src="cloneVideoUrl" controls style="width: 100%;"></video>
      <image :src="cloneCoverUrl" style="width: 200rpx; height: 120rpx; margin-top: 10px;" />
    </view>
    <view v-if="cloneStatus === 'failed'">
      <text>克隆失败，请重试</text>
    </view>
  </view>
</template>

<script>
import config from '@/config.js'
export default {
  data() {
    return {
      videoUrl: '',
      videoFileName: '',
      name: '',
      isCloning: false,
      cloneStatus: '',
      sceneTaskId: '',
      cloneVideoUrl: '',
      cloneCoverUrl: '',
      pollingTimer: null
    }
  },
  methods: {
    chooseVideo() {
      uni.chooseVideo({
        sourceType: ['album', 'camera'],
        maxDuration: 60,
        camera: 'back',
        success: (res) => {
          const tempFilePath = res.tempFilePath;
          this.videoFileName = tempFilePath.split('/').pop();
          this.uploadVideo(tempFilePath);
        }
      });
    },
    uploadVideo(filePath) {
      uni.showLoading({ title: '上传中...' });
      uni.uploadFile({
        url: config.apiBaseUrl + '/api/digital-human/upload-video',
        filePath: filePath,
        name: 'file',
        header: {
          'Authorization': `Bearer ${uni.getStorageSync('token')}`
        },
        success: (res) => {
          uni.hideLoading();
          const data = JSON.parse(res.data);
          if (data.success) {
            this.videoUrl = data.file_url;
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
    startClone() {
      if (!this.videoUrl || !this.name) return;
      this.isCloning = true;
      this.cloneStatus = 'processing';
      uni.request({
        url: config.apiBaseUrl + '/api/digital-human/clone-human',
        method: 'POST',
        header: {
          'Authorization': `Bearer ${uni.getStorageSync('token')}`,
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        data: {
          video_url: this.videoUrl,
          name: this.name
        },
        success: (res) => {
          if (res.data.success) {
            this.sceneTaskId = res.data.scene_task_id;
            this.pollingCloneStatus();
          } else {
            this.isCloning = false;
            uni.showToast({ title: res.data.message || '克隆失败', icon: 'none' });
          }
        },
        fail: () => {
          this.isCloning = false;
          uni.showToast({ title: '克隆失败', icon: 'none' });
        }
      });
    },
    pollingCloneStatus() {
      this.pollingTimer = setInterval(() => {
        uni.request({
          url: config.apiBaseUrl + `/api/digital-human/clone-human-status/${this.sceneTaskId}`,
          method: 'GET',
          header: {
            'Authorization': `Bearer ${uni.getStorageSync('token')}`
          },
          success: (res) => {
            if (res.data.success) {
              const status = res.data.data.status;
              if (status === 'completed') {
                this.cloneStatus = 'completed';
                this.cloneVideoUrl = res.data.data.video_url;
                this.cloneCoverUrl = res.data.data.cover_url;
                this.isCloning = false;
                clearInterval(this.pollingTimer);
                uni.showToast({ title: '克隆完成', icon: 'success' });
              } else if (status === 'failed') {
                this.cloneStatus = 'failed';
                this.isCloning = false;
                clearInterval(this.pollingTimer);
                uni.showToast({ title: '克隆失败', icon: 'none' });
              }
            }
          }
        });
      }, 8000);
    }
  },
  beforeDestroy() {
    if (this.pollingTimer) clearInterval(this.pollingTimer);
  }
}
</script>

<style>
.clone-digital-human-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40rpx 30rpx;
}
.form-section {
  background: #fff;
  border-radius: 20rpx;
  padding: 40rpx;
  margin-bottom: 40rpx;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.1);
}
button {
  margin-bottom: 20rpx;
}
input {
  width: 100%;
  height: 80rpx;
  border: 1rpx solid #ddd;
  border-radius: 10rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  margin-bottom: 20rpx;
  box-sizing: border-box;
}
</style> 