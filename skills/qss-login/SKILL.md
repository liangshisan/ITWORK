---
name: qss-login
description: >
  去哪儿 QSSO 单点登录自动化。当任何操作遇到 QSSO 登录页面时，使用此技能自动登录。
  通过复用已打开的 QSSO 页面 + 浏览器扩展获取 TOTP + 时效安全校验完成登录。
  触发场景：需要登录 qsso.corp.qunar.com、it.corp.qunar.com 等 Qunar 内网系统时。
agent_created: true
---

# QSSO 自动登录

去哪儿网 QSSO 单点登录自动化。当任何操作（如查 ITDB、提交工单等）需要先通过 QSSO 认证时，调用此技能完成登录，无需手动干预。

## 触发时机

当页面导航被重定向到 `qsso.corp.qunar.com/login.php` 时，自动调用此技能。

## 核心流程

1. 在 Edge 已有页面中查找 QSSO 登录页（复用，不新建标签）
2. 检查 TOTP 剩余时间，距刷新 < 10 秒则等待下一周期
3. 通过 CDP 读取「身份验证器」扩展 popup 获取 6 位 OTP
4. 填写 `userId=chenit.liang` + `passCode=PIN+OTP`
5. 点击 `signIn` 提交
6. 等待跳转，确认登录成功（URL 变为 `it.corp.qunar.com`）

## 关键参数

| 参数 | 值 |
|------|-----|
| 用户名 | `chenit.liang` |
| PIN | `123456` |
| TOTP 来源 | Edge 扩展「身份验证器」，扩展 ID `bhghoamapcdpbohphigoooaddinpkbai`，popup 路径 `view/popup.html` |
| TOTP 刷新周期 | 30 秒（标准 TOTP） |
| 安全窗口 | 至少剩余 10 秒才敢填写 | Passcode 格式 |

### Passcode

`PIN` 在前，`OTP` 在后，拼接为 12 位数字串。

## 执行方式

直接运行技能脚本：

```bash
python scripts/qss_login.py
```

也可指定不同的 redirect URL：

```bash
python scripts/qss_login.py --ret "https://qsso.corp.qunar.com/login.php?ret=..."
```

仅获取 OTP 不登录（调试用）：

```bash
python scripts/qss_login.py --check-only
```

## 依赖

- Edge 浏览器已打开（`--remote-debugging-port=9222`）
- QSSO 登录页已存在于 Edge 标签页中
- Playwright 已安装
- Python venv 路径：`D:/Users/chenit.liang/.workbuddy/binaries/python/envs/default/Scripts/python.exe`

## 常见问题

### 登录失败

通常因为 OTP 过期或用户名/PIN 不对。30 秒 TOTP 窗口内有效，安全窗口已保证提交时有充足剩余时间。

### 找不到 QSSO 页面

确认 Edge 已打开 `qsso.corp.qunar.com/login.php`。如果页面不存在，可能已登录或 URL 不正确。

### 扩展读不到 OTP

检查「身份验证器」扩展是否正常加载。通过 CDP target 列表验证扩展 ID 和 popup 路径。
