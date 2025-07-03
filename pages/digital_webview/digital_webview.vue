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
  onLoad() {
    //this.url = config.apiBaseUrl + '/assistant/chat-page'
    this.url ='https://dh.dizhijia.cn'
    //this.url = 'https://dify.dizhijia.cn/chat/aXq8v7OxFYQazTmy'//config.apiBaseUrl //+ '/assistant/chat-page'
  }
}
</script> 