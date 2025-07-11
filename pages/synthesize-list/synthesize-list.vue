<template>
  <view class="synthesize-list-container">
    <!-- 顶部提示 -->
    <view class="tip-bar">
      <uni-icons type="info" size="20" color="#FF6B6B"></uni-icons>
      <text class="tip-text">只显示24小时内的视频，过期自动删除，请尽快下载！</text>
    </view>
    <!-- 视频列表 -->
    <view v-if="videoList.length === 0" class="empty-list">
      <uni-icons type="videocam" size="64" color="#999"></uni-icons>
      <text class="empty-title">暂无合成视频</text>
      <text class="empty-desc">请先合成数字人视频</text>
    </view>
    <view v-else>
      <view v-for="item in videoList" :key="item.video_task_id" class="video-card">
        <image :src="item.cover_url" class="video-cover" mode="aspectFill"></image>
        <view class="video-info">
          <text class="video-time">合成时间: {{ formatTime(item.create_time) }}</text>
          <text class="video-duration">时长: {{ formatDuration(item.duration) }}</text>
          <view class="video-actions">
            <button class="download-btn" @click="downloadVideo(item.video_url)">下载视频</button>
            <button class="play-btn" @click="playVideo(item.video_url)">播放</button>
          </view>
        </view>
      </view>
    </view>
    <!-- 视频播放弹窗 -->
    <uni-popup ref="videoPopup" type="center">
      <view class="popup-video-wrapper">
        <video v-if="currentVideoUrl" :src="currentVideoUrl" controls autoplay class="popup-video"></video>
        <button class="close-btn" @click="closeVideo">关闭</button>
      </view>
    </uni-popup>
  </view>
</template>

<script>
import uniPopup from '@dcloudio/uni-ui/lib/uni-popup/uni-popup.vue'
import config from '@/config.js'
export default {
  components: { uniPopup },
  data() {
    return {
      videoList: [],
      currentVideoUrl: ''
    }
  },
  onShow() {
    this.loadVideoList();
  },
  methods: {
    async loadVideoList() {
      
      try {
        uni.showLoading({ title: '加载中...' });
        const res = await uni.request({
          url: config.apiBaseUrl + '/api/digital-human/synthesize-list',
          method: 'GET',
          header: {
            'Authorization': `Bearer ${uni.getStorageSync('token')}`
          }
        });
        uni.hideLoading();
        if (res.data.success) {
          this.videoList = res.data.data;
        } else {
          uni.showToast({ title: res.data.message || '加载失败', icon: 'none' });
        }
      } catch (e) {
        uni.hideLoading();
        uni.showToast({ title: '加载失败', icon: 'none' });
      }
    },
    formatTime(timeStr) {
      if (!timeStr) return '';
      const date = new Date(timeStr);
      return date.toLocaleString('zh-CN');
    },
    formatDuration(duration) {
      if (!duration) return '';
      const minutes = Math.floor(duration / 60);
      const seconds = Math.floor(duration % 60);
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    },
    async downloadVideo(url) {
      if (!url) return;
      uni.showLoading({ title: '下载中...' });
      try {
        const res = await uni.downloadFile({ url });
        if (res.statusCode === 200) {
          uni.saveVideoToPhotosAlbum({
            filePath: res.tempFilePath,
            success: () => {
              uni.showToast({ title: '保存成功', icon: 'success' });
            },
            fail: () => {
              uni.showToast({ title: '保存失败', icon: 'none' });
            }
          });
        } else {
          uni.showToast({ title: '下载失败', icon: 'none' });
        }
      } catch (e) {
        uni.showToast({ title: '下载失败', icon: 'none' });
      } finally {
        uni.hideLoading();
      }
    },
    playVideo(url) {
      this.currentVideoUrl = url;
      this.$refs.videoPopup.open();
    },
    closeVideo() {
      this.currentVideoUrl = '';
      this.$refs.videoPopup.close();
    }
  }
}
</script>

<style>
.synthesize-list-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
}
.tip-bar {
  display: flex;
  align-items: center;
  background: #fffbe6;
  color: #FF6B6B;
  padding: 20rpx 30rpx;
  font-size: 28rpx;
  border-radius: 0 0 20rpx 20rpx;
  margin-bottom: 30rpx;
}
.tip-text {
  margin-left: 16rpx;
  color: #FF6B6B;
}
.empty-list {
  background: rgba(255,255,255,0.95);
  border-radius: 20rpx;
  padding: 80rpx 40rpx;
  text-align: center;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.1);
  margin: 40rpx;
}
.empty-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin: 20rpx 0 10rpx;
}
.empty-desc {
  font-size: 26rpx;
  color: #666;
  margin-bottom: 40rpx;
}
.video-card {
  background: rgba(255,255,255,0.95);
  border-radius: 20rpx;
  margin: 30rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  padding: 20rpx;
}
.video-cover {
  width: 180rpx;
  height: 120rpx;
  border-radius: 12rpx;
  margin-right: 30rpx;
  background: #f0f0f0;
}
.video-info {
  flex: 1;
}
.video-time, .video-duration {
  display: block;
  font-size: 26rpx;
  color: #666;
  margin-bottom: 8rpx;
}
.video-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 10rpx;
}
.download-btn, .play-btn {
  background: linear-gradient(135deg, #1AAD19 0%, #2ECC71 100%);
  color: #fff;
  border: none;
  border-radius: 30rpx;
  padding: 12rpx 32rpx;
  font-size: 26rpx;
  font-weight: bold;
}
.play-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.popup-video-wrapper {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  display: flex;
  flex-direction: column;
  align-items: center;   /* 水平居中 */
  justify-content: center; /* 垂直居中 */
  min-width: 650rpx;
  min-height: 400rpx;
}
.popup-video {
  width: 600rpx;
  height: 340rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
  display: block;
  margin-left: auto;
  margin-right: auto;
}
.close-btn {
  background: #FF6B6B;
  color: #fff;
  border: none;
  border-radius: 30rpx;
  padding: 12rpx 32rpx;
  font-size: 26rpx;
  font-weight: bold;
}
</style> 