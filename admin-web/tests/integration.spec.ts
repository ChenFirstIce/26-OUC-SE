import { test, expect, type APIRequestContext, type Page } from '@playwright/test'

async function assignment(request: APIRequestContext) {
  const login = await request.post('/api/v1/auth/login', { data: { username: 'doctor1', password: 'Doctor123!' } })
  expect(login.ok()).toBeTruthy()
  const headers = { Authorization: `Bearer ${(await login.json()).access_token}` }
  const patient = await request.post('/api/v1/patients', { headers, data: { patient_code: `E${Date.now()}`, full_name: '浏览器验证虚拟患者' } })
  expect(patient.status()).toBe(201)
  const templates = await (await request.get('/api/v1/questionnaires', { headers })).json()
  const version = templates.find((item: any) => item.code === 'DEMO_SCD').latest_version_id
  const result = await request.post('/api/v1/assignments', { headers, data: {
    patient_id: (await patient.json()).id, questionnaire_version_ids: [version], title: '浏览器闭环测试',
  } })
  expect(result.status()).toBe(201)
  return { ...(await result.json()), headers }
}

async function enter(page: Page, task: any) {
  await page.goto(`/p/fill/${task.token}`)
  await page.getByPlaceholder('6 位访问码').fill(task.access_code)
  await page.getByRole('button', { name: '验证并进入' }).click()
  await expect(page.getByRole('button', { name: '开始填写', exact: true })).toBeVisible()
}

test('手机逐题填写、草稿恢复、历史记录与医生报告', async ({ page, request }, info) => {
  const task = await assignment(request)
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await enter(page, task)
  await page.getByRole('button', { name: '开始填写', exact: true }).click()
  await page.locator('label.el-radio').filter({ hasText: /^否$/ }).click()
  await expect(page.getByText('已自动保存', { exact: true })).toBeVisible()
  await page.reload()
  await page.getByRole('button', { name: '继续填写', exact: true }).click()
  await expect(page.getByRole('radio', { name: '否', exact: true })).toBeChecked()
  await page.getByRole('button', { name: '下一题' }).click()
  await page.getByRole('button', { name: '提交问卷', exact: true }).click()
  await expect(page.getByText('请先完成必答题')).toBeVisible()
  await page.locator('label.el-radio').filter({ hasText: /^没有影响$/ }).click()
  await page.screenshot({ path: info.outputPath('patient-mobile.png'), fullPage: true })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy()
  await page.getByRole('button', { name: '提交问卷', exact: true }).click()
  await page.getByRole('button', { name: '确认提交', exact: true }).click()
  await expect(page.getByText('全部问卷已提交', { exact: false })).toBeVisible()
  await page.getByRole('button', { name: '已完成记录' }).click()
  await expect(page.getByText(/提交时间.*用时/)).toBeVisible()
  await expect(page.getByRole('button', { name: '继续填写' })).toHaveCount(0)
  const report = await request.get(`/api/v1/assignments/${task.id}/items/${task.items[0].id}/result`, { headers: task.headers })
  expect(report.status()).toBe(200)
  expect(errors).toEqual([])
})

test('切换评估链接要求重新验证', async ({ page, request }) => {
  const first = await assignment(request)
  const second = await assignment(request)
  await enter(page, first)
  await page.goto(`/p/fill/${second.token}`)
  await expect(page.getByPlaceholder('6 位访问码')).toHaveValue('')
  await expect(page.getByRole('button', { name: '验证并进入' })).toBeVisible()
  await expect(page.getByRole('button', { name: '开始填写', exact: true })).toHaveCount(0)
})

test('返回列表会保存最后一次回答', async ({ page, request }) => {
  const task = await assignment(request)
  await enter(page, task)
  await page.getByRole('button', { name: '开始填写', exact: true }).click()
  await page.locator('label.el-radio').filter({ hasText: /^是$/ }).click()
  await page.getByRole('button', { name: '返回任务列表', exact: false }).click()
  await page.getByRole('button', { name: '继续填写', exact: true }).click()
  await expect(page.getByRole('radio', { name: '是', exact: true })).toBeChecked()
})

test('医生桌面端主要页面可访问', async ({ page }, info) => {
  await page.setViewportSize({ width: 1440, height: 1000 })
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await page.goto('/login')
  await page.getByRole('button', { name: '登录系统' }).click()
  await expect(page).toHaveURL(/dashboard/)
  for (const path of ['/patients', '/assignments', '/questionnaires', '/dashboard']) {
    await page.goto(path)
    await expect(page.locator('main')).toBeVisible()
  }
  await page.screenshot({ path: info.outputPath('doctor-desktop.png'), fullPage: true })
  expect(errors).toEqual([])
})

test('四项 C/B 演示入口无页面运行错误', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  for (const name of ['scd-interview', 'moca-open-answer', 'boston-naming', 'trail-making']) {
    await page.goto(`http://127.0.0.1:5174/demo/${name}`)
    await expect(page.locator('h1')).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy()
  }
  expect(errors).toEqual([])
})
