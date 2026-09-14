import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  timeout: 45000,
  workers: 1,
  use: { baseURL: 'http://127.0.0.1:5173', viewport: { width: 390, height: 844 }, screenshot: 'only-on-failure' },
})
