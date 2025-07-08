<template>
  <web-view :src="url"></web-view>
</template>

<script>
import config from '@/config.js'
export default {
  data() {
    return {
      url: ''
    }
  },
  onLoad(options) {
    //this.url = config.apiBaseUrl + '/assistant/chat-page'
    //this.url ='https://dh.dizhijia.cn'
    //this.url = 'https://dify.dizhijia.cn/chat/i5qWaOxq1ESuQJ9v'//config.apiBaseUrl //+ '/assistant/chat-page'
    this.url =decodeURIComponent(options.url || '');
  }
}
</script> 