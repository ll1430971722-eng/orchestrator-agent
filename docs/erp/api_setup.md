# 聚水潭 API 接入说明

## 前置条件

1. 拥有聚水潭 ERP 系统账号
2. 在聚水潭开放平台创建应用，获取 `AppKey` 和 `AppSecret`
3. Python 3.8+

## 获取凭证

### 步骤 1：登录开放平台

访问 [聚水潭开放平台](https://open.erp321.com) 或 [open.jushuitan.com](https://open.jushuitan.com)

### 步骤 2：创建应用

1. 进入"应用管理" → "创建应用"
2. 填写应用名称（如 `orchestrator-agent`）
3. 选择应用类型：**自用型应用**（仅自己公司使用）
4. 提交后获取 `AppKey` 和 `AppSecret`

### 步骤 3：配置 .env

```bash
JST_APP_KEY=你的AppKey
JST_APP_SECRET=你的AppSecret
# 可选：如使用沙箱测试环境
# JST_BASE_URL=https://test-open.erp321.com/api
```

## 验证连通性

```bash
python scripts/erp/jst_client.py
python scripts/erp/jst_client.py /open/shops/query
```

## 安全注意

1. `.env` 文件已在 `.gitignore` 中
2. 不要在日志/截图中暴露 AppSecret
3. 只用只读 API：不调用任何写入类接口
4. 不在报告中输出成本/利润的具体数字
