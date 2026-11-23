import { createApp } from 'vue'
import { createPinia } from 'pinia'
// 组件按需引入（vite.config.js）；以函数方式调用的服务需手动引入样式
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/loading/style/css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import '@fontsource-variable/geist'
import '@fontsource-variable/geist-mono'

import App from './App.vue'
import router from './router'
import './styles/index.css'

document.documentElement.classList.add('dark')

const app = createApp(App)

app.use(createPinia())
app.use(router)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
