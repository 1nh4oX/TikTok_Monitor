# 🔐 认证配置指南

本文档说明如何获取并配置抖音 API 所需的认证信息。

## 📋 需要的信息

| 参数 | 说明 | 重要性 |
|------|------|--------|
| Cookie | 浏览器存储的会话信息 | ⭐⭐⭐ 必需 |
| msToken | 认证令牌 | ⭐⭐ 推荐 |
| webid | 设备标识 | ⭐ 可选 |

---

## 🚀 获取步骤

### 第 1 步：打开抖音热榜页面

使用 Chrome 浏览器访问：
```
https://www.douyin.com/hot
```

### 第 2 步：打开开发者工具

- Windows/Linux: 按 `F12` 或 `Ctrl + Shift + I`
- macOS: 按 `Cmd + Option + I`

### 第 3 步：切换到 Network 标签

1. 点击顶部的 **"Network"**（网络）标签
2. 勾选 **"Preserve log"**（保留日志）
3. 刷新页面 (`Ctrl+R` 或 `Cmd+R`)

### 第 4 步：找到 API 请求

在请求列表中，找到名称包含以下内容的请求：
- `list` 
- `hot/search`

![寻找API请求](https://via.placeholder.com/600x200?text=Network标签中找到list请求)

### 第 5 步：复制 Cookie

1. 点击找到的请求
2. 在右侧面板点击 **"Headers"**（标头）
3. 向下滚动找到 **"Request Headers"**（请求标头）
4. 找到 **"Cookie"** 行
5. 复制整个 Cookie 值（可能很长）

### 第 6 步：获取 msToken（可选）

方法一：从 URL 参数获取
1. 查看请求的 URL
2. 找到 `msToken=xxx` 部分

方法二：从 Cookie 获取
1. 在 Cookie 中搜索 `msToken`
2. 复制其值

### 第 7 步：获取 webid（可选）

在请求 URL 中找到 `webid=xxx` 部分并复制。

---

## 📝 配置方法

### 方法 1：编辑配置文件（推荐）

编辑 `backend/config.py` 文件：

```python
# 🍪 Cookie - 从浏览器复制的完整 Cookie
COOKIE = "ttwid=xxx; passport_csrf_token=xxx; ..."

# 🔑 msToken - 重要的认证参数
MSTOKEN = "你的msToken值"

# 🆔 WebID - 设备标识
WEBID = "你的webid值"
```

### 方法 2：环境变量（部署时推荐）

```bash
export DY_COOKIE="你的Cookie"
export DY_MSTOKEN="你的msToken"
export DY_WEBID="你的webid"
```

---

## ⚠️ 注意事项

1. **有效期**: Cookie 和 msToken 有有效期，过期后需要重新获取
2. **隐私安全**: 
   - ❌ 不要分享你的 Cookie 给他人
   - ❌ 不要提交 Cookie 到公开仓库
   - ✅ 使用 `.gitignore` 忽略配置文件
3. **请求频率**: 建议抓取间隔 ≥ 10 分钟，避免被封禁

---

## 🛟 演示模式

如果没有配置认证信息，系统会自动回退到**演示模式**，使用 `mono_finding` 目录下的样本数据。

这对于：
- ✅ 快速预览系统功能
- ✅ 开发测试
- ✅ 向他人演示

非常有用！

---

## ❓ 常见问题

### Q: API 返回 "status_code 非 0" 错误
A: 通常是 Cookie 过期或无效，请重新获取。

### Q: 获取不到 msToken
A: msToken 不是必需的，没有也能运行（可能数据受限）。

### Q: 需要登录抖音账号吗？
A: 不需要。登录账号可能获取更完整的数据，但不登录也能用。
