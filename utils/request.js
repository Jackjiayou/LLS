import config from '@/config.js'

// 请求拦截器
const request = (options) => {
    // 获取token
    const token = uni.getStorageSync('token')
    const tokenExpireTime = uni.getStorageSync('token_expire_time')
    
    // 检查token是否存在且未过期
    if (token && tokenExpireTime && Date.now() < tokenExpireTime) {
        // 添加token到请求头
        options.header = {
            ...options.header,
            'Authorization': `Bearer ${token}`
        }
    } else if (options.url !== '/auth/login') {  // 登录接口不需要token
        // token不存在或已过期，跳转到登录页
        uni.removeStorageSync('token')
        uni.removeStorageSync('token_expire_time')
        uni.removeStorageSync('userInfo')
        
        uni.showToast({
            title: '登录已过期，请重新登录',
            icon: 'none',
            duration: 2000
        })
        
        setTimeout(() => {
            uni.reLaunch({
                url: '/pages/login/login'
            })
        }, 2000)
        
        return Promise.reject(new Error('登录已过期'))
    }
    
    // 添加基础URL
    if (!options.url.startsWith('http')) {
        options.url = `${config.apiBaseUrl}${options.url}`
    }
    
    // 设置默认超时时间
    if (!options.timeout) {
        options.timeout = 30000  // 默认30秒
    }
    
    // 发起请求
    return new Promise((resolve, reject) => {
        uni.request({
            ...options,
            success: (res) => {
                // 处理响应
                if (res.statusCode === 401) {
                    // token无效，跳转到登录页
                    uni.removeStorageSync('token')
                    uni.removeStorageSync('token_expire_time')
                    uni.removeStorageSync('userInfo')
                    
                    uni.showToast({
                        title: '登录已过期，请重新登录',
                        icon: 'none',
                        duration: 2000
                    })
                    
                    setTimeout(() => {
                        uni.reLaunch({
                            url: '/pages/login/login'
                        })
                    }, 2000)
                    
                    reject(new Error('登录已过期'))
                } else {
                    resolve(res)
                }
            },
            fail: (err) => {
                // 处理错误
                let errorMsg = '请求失败'
                if (err.errMsg.includes('timeout')) {
                    errorMsg = '请求超时，请检查网络连接'
                } else if (err.errMsg.includes('fail')) {
                    errorMsg = '网络连接失败，请检查网络设置'
                }
                
                uni.showToast({
                    title: errorMsg,
                    icon: 'none',
                    duration: 2000
                })
                
                reject(err)
            }
        })
    })
}

export default request 