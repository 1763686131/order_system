import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import tableLayout from './directives/tableLayout'
import './assets/styles/main.css'
import './assets/styles/resizable-columns.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.directive('table-layout', tableLayout)
app.directive('resizable-columns', tableLayout)
app.mount('#app')
