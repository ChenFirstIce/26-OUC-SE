import axios from 'axios'

export const api = axios.create({ baseURL: '/api/v1', timeout: 15000 })

api.interceptors.request.use((config) => {
  const patientRoute = window.location.pathname.startsWith('/p/')
  const token = patientRoute ? sessionStorage.getItem('patient_token') : localStorage.getItem('staff_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(new Error(error.response?.data?.message || error.message || '请求失败')),
)

