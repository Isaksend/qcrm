import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { i18n } from './i18n'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(i18n)
app.use(router)

// Дождаться первой навигации (в т.ч. редиректа с `/` на `/login` без токена),
// иначе App.vue успевает отрисовать CRM до срабатывания beforeEach.
void router.isReady().then(() => {
  app.mount('#app')
})
