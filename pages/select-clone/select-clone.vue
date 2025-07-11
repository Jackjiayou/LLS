<template>
  <view class="select-clone-container">
    <!-- 顶部标题栏 -->
    <view class="header">
      <view class="header-left" @click="goBack">
        <uni-icons type="left" size="24" color="#fff"></uni-icons>
      </view>
      <text class="title">选择分身</text>
      <view class="header-right"></view>
    </view>
    
    <!-- 主要内容区域 -->
    <view class="content">
      <!-- 说明文字 -->
      <view class="intro-section">
        <text class="intro-title">选择数字人分身</text>
        <text class="intro-desc">请选择要用于合成的数字人分身</text>
      </view>
      
      <!-- 分身列表 -->
      <view class="clone-list">
        <view v-if="cloneList.length === 0" class="empty-list">
          <uni-icons type="info" size="64" color="#999"></uni-icons>
          <text class="empty-title">暂无分身</text>
          <text class="empty-desc">请先克隆数字人分身</text>
          <button class="create-btn" @click="goToCloneHuman">去克隆分身</button>
        </view>
        
        <view v-else>
          <view 
            v-for="clone in cloneList" 
            :key="clone.scene_task_id"
            class="clone-item"
            :class="{ 'selected': selectedClone && selectedClone.scene_task_id === clone.scene_task_id }"
            @click="selectClone(clone)"
          >
            <!-- 分身封面 -->
            <view class="clone-cover">
              <image 
                v-if="clone.cover_url" 
                :src="clone.cover_url" 
                class="cover-image" 
                mode="aspectFill"
              ></image>
              <view v-else class="cover-placeholder">
                <uni-icons type="videocam" size="32" color="#999"></uni-icons>
              </view>
              
              <!-- 状态标签 -->
              <view class="status-badge" :class="clone.status">
                {{ getStatusText(clone.status) }}
              </view>
            </view>
            
            <!-- 分身信息 -->
            <view class="clone-info">
              <text class="clone-name">{{ clone.name }}</text>
              <text class="clone-time">创建时间: {{ formatTime(clone.create_time) }}</text>
            </view>
            
            <!-- 选择指示器 -->
            <view v-if="selectedClone && selectedClone.scene_task_id === clone.scene_task_id" class="select-indicator">
              <uni-icons type="checkmarkempty" size="24" color="#1AAD19"></uni-icons>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 确认按钮 -->
      <view v-if="cloneList.length > 0" class="action-section">
        <button 
          class="confirm-btn" 
          :class="{ 'disabled': !selectedClone }"
          :disabled="!selectedClone"
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

export default {
  data() {
    return {
      cloneList: [],
      selectedClone: null
    };
  },
  onLoad() {
    this.loadCloneList();
  },
  methods: {
    goBack() {
      uni.navigateBack();
    },
    
    // 加载分身列表
    async loadCloneList() {
      try {
        uni.showLoading({ title: '加载中...' });
        
        const response = await uni.request({
          url: config.apiBaseUrl + '/api/digital-human/clones',
          method: 'GET',
          header: {
            'Authorization': `Bearer ${uni.getStorageSync('token')}`
          }
        });
        
        uni.hideLoading();
        
        if (response.data.success) {
          this.cloneList = response.data.data;
        } else {
          uni.showToast({
            title: response.data.message || '加载失败',
            icon: 'none'
          });
        }
      } catch (error) {
        uni.hideLoading();
        console.error('加载分身列表失败:', error);
        uni.showToast({
          title: '加载分身列表失败',
          icon: 'none'
        });
      }
    },
    
    // 选择分身
    selectClone(clone) {
      if (clone.status !== 'completed') {
        uni.showToast({
          title: '只能选择已完成的分身',
          icon: 'none'
        });
        return;
      }
      this.selectedClone = clone;
    },
    
    // 确认选择
    confirmSelection() {
      if (!this.selectedClone) return;
      
      // 返回上一页并传递选中的分身
      const pages = getCurrentPages();
      const prevPage = pages[pages.length - 2];
      
      if (prevPage && prevPage.$vm) {
        prevPage.$vm.selectedClone = this.selectedClone;
      }
      
      uni.navigateBack();
    },
    
    // 跳转到克隆分身页面
    goToCloneHuman() {
      uni.navigateTo({
        url: '/pages/clone-digital-human/clone-digital-human'
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
  }
}
</script>

<style>
.select-clone-container {
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

.clone-list {
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
  background: linear-gradient(135deg, #1AAD19 0%, #2ECC71 100%);
  color: #fff;
  border: none;
  border-radius: 44rpx;
  padding: 20rpx 40rpx;
  font-size: 28rpx;
  font-weight: bold;
}

.clone-item {
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

.clone-item.selected {
  border: 3rpx solid #1AAD19;
  background: rgba(26, 173, 25, 0.05);
}

.clone-item:active {
  transform: scale(0.98);
}

.clone-cover {
  position: relative;
  margin-right: 30rpx;
}

.cover-image,
.cover-placeholder {
  width: 120rpx;
  height: 120rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
}

.status-badge {
  position: absolute;
  top: -10rpx;
  right: -10rpx;
  padding: 6rpx 12rpx;
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

.clone-info {
  flex: 1;
}

.clone-name {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 12rpx;
}

.clone-time {
  font-size: 24rpx;
  color: #666;
  display: block;
}

.select-indicator {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(26, 173, 25, 0.1);
  border-radius: 30rpx;
}

.action-section {
  margin-top: 40rpx;
}

.confirm-btn {
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

.confirm-btn.disabled {
  background: #ccc;
  box-shadow: none;
}

.confirm-btn:active {
  transform: scale(0.98);
}
</style> 