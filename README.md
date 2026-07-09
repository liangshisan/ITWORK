# 梁十三 IT 运维智能体

去哪儿网（成都茂业）IT 运维自动化助手。通过对话自动完成工单提交、资产出入库、邮箱开通查询、远程码推送等日常工作。

仓库地址：https://github.com/liangshisan/ITWORK

## 包含内容

| 模块 | 说明 |
|------|------|
| agents/liang-shisan-agent.md | 智能体定义（角色、意图路由、铁律） |
| skills/feishu-workorder/ | 飞书工单自动填写+提交 |
| skills/asset-barcode/ | 资产条形码识别 + 出入库 |
| skills/email-manager/ | 邮箱查询 + 自动开通 |
| skills/sunflower-remote/ | 向日葵远程码推送 |
| .codebuddy-plugin/plugin.json | 专家包注册信息 |

## 快速使用

### 方式一：作为 WorkBuddy 专家包

```bash
git clone https://github.com/liangshisan/ITWORK.git
cp -r ITWORK ~/.workbuddy/plugins/marketplaces/my-experts/plugins/liang-shisan-agent/
python3 scripts/register_expert.py ~/.workbuddy/plugins/marketplaces/my-experts/plugins/liang-shisan-agent/
```

### 方式二：单独运行技能脚本

各技能目录含 SKILL.md + 可直接运行的 .py。例如工单：

```bash
pip install playwright
python -m playwright install chromium
python skills/feishu-workorder/fill_form.py --reporter 张三 --category1 硬件支持 ...
python skills/feishu-workorder/submit_form.py --confirm yes
```

## 运行环境

- Windows 10/11 + Edge（--remote-debugging-port=9222）
- Python 3.10+
- Playwright / pyautogui / Pillow
- 内网：飞书表单、金山文档、AD工具、ITDB、QSSO

## 技能一览

- 飞书工单：识别 IT 问题 → 填 15 字段 → 验证 → 提交
- 资产出入库：条形码 OCR → 分类 → 填金山文档 → 验证备份
- 邮箱管理：AD 查询 → 未开通自动开通
- 远程码：推送向日葵识别码+验证码到微信

详见各 skills/*/SKILL.md。
