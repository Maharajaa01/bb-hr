import { MotionPlugin } from "@vueuse/motion"
import { createPinia } from "pinia"
import { createApp } from "vue"

import App from "./App.vue"
import { registerServiceWorker } from "./lib/pwa"
import { router } from "./router"
import "./style.css"

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(MotionPlugin)
app.mount("#app")

registerServiceWorker()
