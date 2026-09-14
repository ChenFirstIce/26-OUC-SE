import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {
  ElButton, ElCheckbox, ElCheckboxGroup, ElConfigProvider, ElDatePicker, ElDialog, ElEmpty,
  ElForm, ElFormItem, ElInput, ElInputNumber, ElLoading, ElOption, ElRadio, ElRadioGroup,
  ElSelect, ElSwitch, ElTable, ElTableColumn, ElTabPane, ElTabs, ElTag, ElTimePicker, ElUpload,
} from 'element-plus'
import 'element-plus/es/components/base/style/css'
import 'element-plus/es/components/button/style/css'
import 'element-plus/es/components/checkbox/style/css'
import 'element-plus/es/components/checkbox-group/style/css'
import 'element-plus/es/components/config-provider/style/css'
import 'element-plus/es/components/date-picker/style/css'
import 'element-plus/es/components/dialog/style/css'
import 'element-plus/es/components/empty/style/css'
import 'element-plus/es/components/form/style/css'
import 'element-plus/es/components/form-item/style/css'
import 'element-plus/es/components/input/style/css'
import 'element-plus/es/components/input-number/style/css'
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/option/style/css'
import 'element-plus/es/components/radio/style/css'
import 'element-plus/es/components/radio-group/style/css'
import 'element-plus/es/components/select/style/css'
import 'element-plus/es/components/switch/style/css'
import 'element-plus/es/components/table/style/css'
import 'element-plus/es/components/table-column/style/css'
import 'element-plus/es/components/tab-pane/style/css'
import 'element-plus/es/components/tabs/style/css'
import 'element-plus/es/components/tag/style/css'
import 'element-plus/es/components/time-picker/style/css'
import 'element-plus/es/components/upload/style/css'
import './styles.css'
import './advanced.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
const components = [
  ElButton, ElCheckbox, ElCheckboxGroup, ElConfigProvider, ElDatePicker, ElDialog, ElEmpty,
  ElForm, ElFormItem, ElInput, ElInputNumber, ElOption, ElRadio, ElRadioGroup, ElSelect,
  ElSwitch, ElTable, ElTableColumn, ElTabPane, ElTabs, ElTag, ElTimePicker, ElUpload,
]
for (const component of components) app.component(component.name!, component)
app.use(ElLoading).use(createPinia()).use(router).mount('#app')
