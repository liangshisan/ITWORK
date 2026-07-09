---
name: sunflower-remote
description: 向日葵远程码获取。当用户说"远程码""向日葵""连一下""远程"等意图时触发。启动向日葵客户端并推送识别码+验证码到微信。
version: 1.0
agent_created: true
---

# 向日葵远程码获取技能

## 触发词
- "远程码"、"向日葵"、"连一下"、"远程连接"、"我要远程"

## 固定信息
- **识别码**：399 584 421
- **长期验证码**：axfop7
- **向日葵路径**：C:\Program Files\Oray\SunLogin\SunloginClient\SunloginClient.exe
- **启动参数**：`--mod=autorun`

## 执行步骤

### Step 1: 检查向日葵是否运行
```bash
tasklist | grep -i sunlogin
```
如果 `SunloginClient.exe` 已有 Services 实例 → 跳到 Step 3

### Step 2: 启动向日葵
```bash
"C:/Program Files/Oray/SunLogin/SunloginClient/SunloginClient.exe" --mod=autorun &
```
等待 5 秒让其启动

### Step 3: 验证进程
```bash
sleep 5 && tasklist | grep -i sunlogin
```
确认至少有 `SunloginClient.exe` (Services) 和 `sunlogin_guard.exe` 进程

### Step 4: 推送到微信
```bash
python wechat_forward.py send "向日葵已启动 ✅

🔑 识别码：399 584 421
🔐 验证码：axfop7"
```

## 注意事项
- 向日葵已开启无人值守模式 + 固定验证码，锁屏状态也能连接
- 不需要解锁电脑
- 验证码为长期固定码，不会变化
- 识别码 399 584 421 是固定的设备识别码
