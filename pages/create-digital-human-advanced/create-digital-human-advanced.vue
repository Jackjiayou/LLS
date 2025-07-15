// ... existing code ...
<template>
  <view class="create-digital-human-advanced-container">
    <!-- 协议弹窗 -->
    <view v-if="showAgreement" class="agreement-modal">
      <view class="agreement-content">
        <text class="agreement-title">数字人使用协议</text>
        <scroll-view scroll-y="true" class="agreement-body">
          <view class="agreement-paragraph">
            本声明将帮助您更好地在本平台使用相关工具上传和管理您的作品。您若上传作品，即视为您已充分知悉并充分接受以下内容：
          </view>
          <view class="agreement-paragraph">
            1. 您作为使用者在本平台上传、发布的作品，应具有独立、完整的知识产权，不得侵犯他人知识产权等任何权利。
          </view>
          <view class="agreement-paragraph">
            2. 您在使用本平台及上传、发布作品时，应当自觉遵守国家法律、法规，遵守公共秩序，尊重社会公德、社会主义制度、国家利益、公民合法权益、道德风尚和信息真实性等要求。如有违反，一经本平台发现将根据违规程度采取包括但不限于删除、下架、禁止发布内容、封禁账号等处理方式。如造成恶劣影响或涉嫌违法犯罪的，本平台将有权向有关管理机关或公安机关提交相关内容，并配合进行调查。
          </view>
          <view class="agreement-paragraph">
            3. 若您上传的作品及作品中的素材（包括但不限于创意、文本、肖像、音频、图片、视频等）侵犯了任何第三方权利，本平台均有权在收到相关侵权投诉后对该被投诉的作品或用户账号依据相应规则，采取包括但不限于下架、警告、封禁账号等处理方式。
          </view>
        </scroll-view>
        <view class="agreement-actions">
          <button @click="onCancel" class="cancel-btn">取消</button>
          <button type="primary" @click="onAgree" class="agree-btn">我已知晓，同意</button>
        </view>
      </view>
    </view>
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
        <text class="intro-title">数字人制作方式</text>
        <text class="intro-desc">克隆数字人分身->克隆音色->合成数字人</text>
      </view>
      <!-- 功能按钮区域 -->
      <view class="function-section">
        <!-- 克隆数字人 -->
        <view class="function-item" @click="goToCloneHuman">
          <view class="function-icon">
            <uni-icons type="videocam" size="32" color="#FF6B6B"></uni-icons>
          </view>
          <view class="function-content">
            <text class="function-title">克隆数字人分身</text>
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
      showAgreement: true // 默认显示协议弹窗
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
    },
    onAgree() {
      this.showAgreement = false;
      // 可选：uni.setStorageSync('agreed_digital_human', true);
    },
    onCancel() {
      uni.navigateBack();
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
/* 协议弹窗样式 */
.agreement-modal {
  position: fixed;
  left: 0; top: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.agreement-content {
  width: 80vw;
  max-height: 80vh;
  background: #fff;
  border-radius: 20rpx;
  padding: 32rpx 24rpx 16rpx 24rpx;
  display: flex;
  flex-direction: column;
}
.agreement-title {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 16rpx;
  text-align: center;
  color: #222;
}
.agreement-body {
  flex: 1;
  overflow-y: auto;
  font-size: 26rpx;
  color: #333;
  margin-bottom: 24rpx;
  max-height: 50vh;
}
.agreement-paragraph {
  margin-bottom: 18rpx;
  line-height: 1.7;
  text-align: left;
}
.agreement-actions {
  display: flex;
  justify-content: space-between;
  gap: 24rpx;
}
.cancel-btn {
  background: #f5f5f5;
  color: #666;
}
.agree-btn {
  background: #007aff;
  color: #fff;
}
/* ... existing code ... */
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