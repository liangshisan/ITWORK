---
name: email-manager
description: 邮箱状态查询与手动开通。当用户说"查一下这个账号""查一下邮箱""帮我查一下XX"等意图时触发。自动查询AD中邮箱状态，若未开通则自动执行开通流程。
agent_created: true
mode: craft
---

# 邮箱查询 & 开通技能

## 触发词
- "帮我查一下这个账号" / "查一下这个账号"
- "查一下邮箱" / "查一下 XX"（XX = 账号或邮箱地址）

## 账号提取规则
- 输入含 `@qunar.com` → 去掉域名取前缀（如 `qiang.zuo@qunar.com` → `qiang.zuo`）
- 输入不含 `@qunar.com` → 直接使用作为账号

## 完整流程

### Step 0: 环境准备
1. 检查 AD 工具是否运行（窗口标题含 `查询AD` 或 `AD`）
2. 未运行 → `Start-Process "D:\Users\chenit.liang\Desktop\查询AD用户及组-2022-8-22.exe"`
3. 等待窗口出现后 **最大化**（ShowWindow + SW_MAXIMIZE=3），全屏坐标 (0,0)-(1920,1200)，不再偏移

### Step 1: AD 查询 → `python scripts/ad_query.py <account>`
**前置：** PowerShell `Set-Clipboard -Value '<账号>'`（cmd `type|clip` 不行）

脚本自动执行：
1. 激活 AD 窗口 + 确保最大化
2. 点击「用户登录名」输入框 → Ctrl+A → Ctrl+V 粘贴账号
3. 点击「查询邮箱相关属性」复选框
4. 点击「查询」按钮
5. 等待 12 秒 → 截图保存到 `ad_query_result.png`
6. **检查截图内容**：读取截图，若所有字段（登录名、显示名、邮件地址等）均为空 → 等待 3 秒后重新截图
7. 重复截图直到出现内容，最多重试 3 次

### Step 2: 结果报告
**基础 6 项（首次输出）：**
| 字段 | 来源 |
|------|------|
| 登录名 | AD 截图 |
| 显示名 | AD 截图 |
| 邮件地址 | 有值=已开通，空=❌未开通 |
| 密码过期 | AD 截图 |
| 账户锁定 | AD 截图 |
| 在职状态 | AD 截图 |

**如果已开通且用户要求详情，补充：**
| 字段 | 来源 |
|------|------|
| 邮箱使用容量(MB) | AD 截图 |
| 邮箱禁止收发配额(MB) | AD 截图 |
| 邮箱使用百分比(%) | AD 截图 |

注意：部分账号 AD 不返回 Exchange 配额数据，显示空白是正常的。

### Step 3: 邮箱开通（仅未开通时触发）
1. Playwright CDP 连接 Edge `http://127.0.0.1:9222`
2. **使用已有标签页**导航（不要 `browser.new_page()` 会丢登录态）
3. URL: `https://it.corp.qunar.com/itworkstation/it/open_email.html`
4. `input[type=text]` fill 账号 → 点击「提交」按钮 → 等待 3 秒 → 截图确认
5. 报告开通结果

### Step 4: 结果输出
- 未开通 → 先报未开通信息 → 自动执行开通 → 截图确认
- 已开通 → 报基础 6 项 + 邮箱用量详情

## AD 工具坐标（全屏模式，已校准）
窗口最大化后 origin (0,0)，坐标 = 绝对鼠标位置：

| 控件 | 坐标 |
|------|------|
| 用户登录名输入框 | (166, 149) |
| 查询按钮 | (382, 145) |
| 邮箱复选框 | (553, 153) |
| 等待时间 | 12 秒 |

> 复选框坐标加了 +4px 补偿（鼠标箭头尖 → 复选框中心），因为 pyautogui 以箭头尖为基准。

## 踩坑记录（禁止重复犯错）
1. ❌ `cmd echo xxx | clip` 会吞点号 → ✅ 用 `PowerShell Set-Clipboard`
2. ❌ 新建标签页 `browser.new_page()` 丢登录态 → ✅ 导航已有标签页
3. ❌ 截图太快结果未加载 → ✅ 查询后等 12 秒
4. ❌ 默认窗口坐标每次偏移 → ✅ 全屏模式，origin 固定 (0,0)
5. ❌ 复选框没勾上 → ✅ 用户重新校准 + 坐标加 +4px 偏移补偿箭头尖
6. ❌ `agent-browser` 新开浏览器无登录态 → ✅ 用 Playwright CDP 连 Edge 已有实例
7. ❌ 第一次查询漏装依赖 → ✅ pyautogui + Pillow + requests 已装
8. ❌ 截图后字段全空以为是查不到 → ✅ AD 加载慢，等 3 秒重新截图，最多重试 3 次

## 文件结构
```
~/.workbuddy/skills/email-manager/
├── SKILL.md               ← 本文档
└── scripts/
    ├── ad_query.py         ← AD 查询（pyautogui 操控桌面工具）
    └── email_open.py       ← 邮箱开通（Playwright CDP 操控网页）
```

## 依赖清单
| 依赖 | 用途 | 安装方式 |
|------|------|----------|
| Python 3.13.12 | 运行环境 | 已装 managed |
| pyautogui | 桌面 GUI 操控 | `pip install pyautogui` |
| Pillow | 截图支持 | `pip install Pillow` |
| requests | HTTP 请求 | `pip install requests` |
| playwright | CDP 浏览器控制 | `pip install playwright` |
| PowerShell | 剪贴板操作 | 系统自带 |
| 查询AD用户及组-2022-8-22.exe | AD 查询 | `D:\Users\chenit.liang\Desktop\` |
| 微信消息转发 | 推送结果 | `wechat_forward.py`（仓库根目录，需改 `BOT_TOKEN`/`TO_USER` 为你的微信配置） |
