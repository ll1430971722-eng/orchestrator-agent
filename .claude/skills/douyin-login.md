# Skill: douyin-login

## 触发条件

当需要登录抖店商家后台（fxg.jinritemai.com）时使用。首次运行 fetch 数据前必须执行。

## 功能

使用 Playwright MCP 打开浏览器，导航到抖店商家后台，处理登录流程，保存登录态供后续使用。

## 前置条件

- Playwright MCP 已配置并可用
- `.env` 中配置了 `DOUYIN_LOGIN_ACCOUNT` 和 `DOUYIN_LOGIN_PASSWORD`（可选，手动登录也支持）

## 步骤

### Step 1: 打开抖店登录页

```
browser_navigate → https://fxg.jinritemai.com/login/common
```

等待页面加载完成。

### Step 2: 检测登录状态

用 `browser_snapshot` 获取页面结构，判断：

- **已有登录态**（页面直接跳转到后台首页，URL 不含 `/login`）
  → 登录态有效，跳到 Step 6 保存截图

- **在登录页**（看到登录表单）
  → 继续 Step 3

### Step 3: 尝试自动登录

如果 `.env` 中有凭证：

1. 用 `browser_snapshot` 找到账号输入框（通常是 `input[type="text"]` 或 placeholder 含"手机号"的 input）
2. `browser_type` 输入 `DOUYIN_LOGIN_ACCOUNT`
3. 找到密码输入框 → `browser_type` 输入 `DOUYIN_LOGIN_PASSWORD`
4. 找到登录按钮 → `browser_click`
5. `browser_wait_for` 等待页面跳转或出现验证码

### Step 4: 处理验证码

如果出现验证码（滑块/图片验证/短信验证）：

1. `browser_screenshot` 截图保存到 `data/screenshots/login_captcha.png`
2. **提示用户手动完成验证码**
3. 轮询检测页面变化（每 3 秒 `browser_snapshot` 一次），直到：
   - 页面跳转到后台首页（URL 不含 `/login`）→ 登录成功
   - 超时 5 分钟 → 登录失败

```
提示模板：
  ┌──────────────────────────────────────┐
  │ 🔐 检测到验证码，请在浏览器中手动完成  │
  │ 完成后脚本会自动检测继续...           │
  └──────────────────────────────────────┘
```

### Step 5: 手动登录（兜底）

如果自动登录失败或未配置凭证：

1. 确保浏览器窗口可见
2. 提示用户在浏览器中手动登录
3. 轮询检测登录状态（同 Step 4 轮询逻辑）
4. 登录成功后自动继续

### Step 6: 确认登录成功

1. `browser_screenshot` 保存到 `data/screenshots/login_success.png`
2. 确认页面包含抖店后台元素（导航菜单、数据概览等）
3. 输出：`✅ 已成功登录抖店后台`

### Step 7: 保存登录态

Playwright MCP 的 persistent context 会自动保存 cookie/localStorage。
无需额外操作，后续会话可直接复用。

## 输出

- 截图：`data/screenshots/login_page.png`（登录页）
- 截图：`data/screenshots/login_success.png`（登录成功确认）
- 登录态：由 Playwright MCP 自动管理

## 安全规则

- ✅ 只做登录操作（认证层面），不修改任何店铺数据
- ✅ 凭证从 `.env` 读取，不写死在 Skill 中
- ❌ 不要在日志中打印账号密码
- ❌ 不要把登录截图发给任何外部服务
