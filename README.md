# 梁十三 IT 运维智能体

去哪儿网（成都茂业）IT 运维自动化助手。通过对话自动完成工单提交、资产出入库、邮箱开通查询、远程码推送等日常工作。

仓库地址：https://github.com/liangshisan/ITWORK

## 快速上手（三步）

1. **下载**：点页面右上角绿色 `Code` → `Download ZIP` → 解压到任意位置
2. **启动 Edge（必须）**：把 `Edge-Debug-9222.lnk` 复制到桌面双击，它会打开一个带 `--remote-debugging-port=9222` 的 Edge 窗口（工单填写、金山文档出入库都依赖这个端口）
3. **装专家包**：把解压后的全部文件复制到
   `C:\Users\你的用户名\.workbuddy\plugins\marketplaces\my-experts\plugins\liang-shisan-agent\`
   重启 / 重载 WorkBuddy，即可在专家列表看到「梁十三智能体」

> 图文版见 `上手说明.md`

## 包含内容

| 模块 | 说明 |
|------|------|
| agents/liang-shisan-agent.md | 智能体定义（角色、意图路由、铁律） |
| skills/feishu-workorder/ | 飞书工单自动填写+提交 |
| skills/asset-barcode/ | 资产条形码识别 + 出入库 |
| skills/email-manager/ | 邮箱查询 + 自动开通 |
| skills/sunflower-remote/ | 向日葵远程码推送 |
| .codebuddy-plugin/plugin.json | 专家包注册信息 |
| Edge-Debug-9222.lnk | 带 9222 调试端口的 Edge 快捷方式（自动化填表必备，双击即用） |
| wechat_forward.py | 微信消息推送工具（仓库根目录，需改 `BOT_TOKEN`/`TO_USER` 为你的微信配置） |

## 快速使用

### 方式一：作为 WorkBuddy 专家包

```bash
git clone https://github.com/liangshisan/ITWORK.git
cp -r ITWORK/. ~/.workbuddy/plugins/marketplaces/my-experts/plugins/liang-shisan-agent/
```
> 复制完成后重启 / 重载 WorkBuddy，即可在专家列表看到「梁十三智能体」。

### 方式二：单独运行技能脚本

各技能目录含 SKILL.md + 可直接运行的 .py。例如工单：

```bash
pip install playwright
python -m playwright install chromium
python skills/feishu-workorder/fill_form.py --reporter 张三 --category1 硬件支持 ...
python skills/feishu-workorder/submit_form.py --confirm yes
```

## 运行环境

- Windows 10/11 + Edge（必须带 `--remote-debugging-port=9222` 调试端口；仓库已附 `Edge-Debug-9222.lnk`，复制到桌面双击即可启动带端口的 Edge）
- Python 3.10+
- Playwright / pyautogui / Pillow
- 内网：飞书表单、金山文档、AD工具、ITDB、QSSO

## 技能一览

- 飞书工单：识别 IT 问题 → 填 15 字段 → 验证 → 提交
- 资产出入库：条形码 OCR → 分类 → 填金山文档 → 验证备份
- 邮箱管理：AD 查询 → 未开通自动开通
- 远程码：推送向日葵识别码+验证码到微信

详见各 skills/*/SKILL.md。
