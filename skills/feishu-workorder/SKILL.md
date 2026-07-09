---
name: feishu-workorder
description: >
  飞书工单自动填写与提交完整流程。当用户说"提工单"、"帮我提个单"、"填工单"等意图时触发。
  包含 fill_form.py（填写）和 submit_form.py（提交）两个脚本，以及所有禁忌规则。
  绝对禁止修改 workorder_lib.py 的核心逻辑，绝对禁止操作 Edge 进程。
agent_created: true
---

# 飞书工单自动填写与提交

本 skill 描述提工单的完整流程、脚本位置、禁忌规则。严格按照本文件操作，不得即兴发挥。

## 脚本位置

三个脚本都在 **本技能目录下**（和 SKILL.md 同一文件夹）：

| 文件 | 说明 |
|------|------|
| `workorder_lib.py` | 核心库，**禁止修改核心逻辑** |
| `fill_form.py` | 填写入口，支持命令行参数或硬编码 |
| `submit_form.py` | 提交脚本 |

> 脚本运行需要 Playwright + Python venv。详见下方「依赖」章节。

### 使用时执行命令

```bash
# 使用本地 Python venv 运行（推荐）
python fill_form.py --reporter "报修人" --category1 "..." ...
python submit_form.py
```

> 辰哥本机 venv 路径：`D:/Users/chenit.liang/.workbuddy/binaries/python/envs/default/Scripts/python.exe`

---

## 完整流程（6步，缺一不可）

### 第1步：运行 fill_form.py 填写

**优先使用命令行参数**，不修改文件内容：

```bash
python fill_form.py \
  --reporter "报修人搜索词" \
  --category1 "一级分类" \
  --category2 "二级分类" \
  --phenomenon "问题现象" \
  --cause "问题原因" \
  --steps "处理步骤" \
  --accept_date "YYYY/MM/DD" \
  --accept_time "HH:MM" \
  --close_date "YYYY/MM/DD" \
  --close_time "HH:MM"
```

**参数说明：**

| 参数 | 说明 | 注意事项 |
|------|------|----------|
| `--reporter` | 报修人搜索词（飞书账号或中文名） | **只给名字就直接用名字搜，不要自己编造账号格式！** |
| `--category1` | 一级分类 | 如"安全软件"、"硬件支持"、"不能体现工单"等 |
| `--category2` | 二级分类 | 用关键词子串匹配即可（如"WIFI测试"能匹配"巡检类-WIFI测试"） |
| `--phenomenon` | 问题现象 | **不少于5个字符** |
| `--cause` | 问题原因 | **不少于5个字符** |
| `--steps` | 处理步骤 | shell中用多行引号传入即可实现换行 |
| `--accept_date` | 接单日期 | 格式 YYYY/MM/DD |
| `--accept_time` | 接单时间 | 格式 HH:MM |
| `--close_date` | 关单日期 | 格式 YYYY/MM/DD |
| `--close_time` | 关单时间 | 格式 HH:MM |

**时间规则**：用户说"3点"= 15:00，"7点半"= 19:30（8点之前一律默认为下午）。

**处理步骤换行**：workorder_lib.py 已内置 `Shift+Enter` 方案，shell 中用多行引号传入即可实现真正换行：
```bash
--steps "1.第一步内容
2.第二步内容
3.第三步内容"
```
> 底层原理：逐行 `keyboard.type()` 输入，行之间用 `Shift+Enter` 软换行，最后触发 InputEvent。不要用 `fill()`（会把 `\n` 当字面字符），也不要用 `innerHTML`（内容不在填写层，表单不识别）。

### 第2步：验证填写结果（必须！）

脚本运行完后，**必须读取结果文件**展示给用户确认：

```bash
# 读取最新的结果文件（脚本生成在当前目录）
cat $(ls -t fill_result_*.txt | head -1)
```

结果文件已内置页面实际值验证（`workorder_lib.py` 2026-05-21 更新）：
- 每个字段一行：`[字段名] 预期:xxx | 实际:xxx | PASS/FAIL`
- **实际值是直接从页面 DOM 读取的**，不是复述参数
- 逐字段检查 PASS/FAIL 状态即可，**不需要再单独跑抓取脚本**

**绝对不能**只口头复述参数就当验证了！必须读取结果文件，逐字段展示预期值和实际值对比。

### 第3步：用户确认后运行 submit_form.py

用户确认填写内容无误后，再运行提交脚本：

```bash
python submit_form.py --confirm yes
```

> ⚠️ **硬性拦截**：自 2026-07-08 起，submit_form.py 强制要求 `--confirm yes` 参数。不传该参数会直接拒绝提交并打印拦截提示。这是技术层面的防自动提交机制——确保只有收到用户明确「提交」指令后才能执行。

### 第4步：验证提交结果

读取 `fill_result.txt` 查看提交结果（"提交成功"或失败原因）。

### 第5步：告知用户结果 + 记录日志

将提交结果用中文清晰告知用户，并更新当天的 memory 日志。

---

## 禁忌规则（违反任意一条都是严重错误）

1. **绝不修改 workorder_lib.py 的核心逻辑** — 这个文件是核心库，改错一次就崩，只看不动
2. **绝不杀/重启 Edge 进程** — 连不上 9222 就提示用户手动开，不允许任何自动操作
3. **绝不在填写前提交** — 必须先 fill 再 submit，两个脚本分开跑
4. **绝不用 Bash 判断 Edge 是否打开** — Bash 环境下 PowerShell 命令输出乱码，会误判
5. **填完必须从结果文件验证** — 不能只口头复述参数，要读结果文件确认每个字段
6. **Python 必须用完整路径** — 不能用 `python` 命令（会指向 WindowsApps 占位符）
7. **不要自己编造飞书账号！** — 辰哥只给名字时，直接用名字搜索，不要瞎拼账号格式（如"殷俏"不能拼成qianqq.yin）
8. **提交按钮定位必须精确** — 遍历所有 button，精确匹配 text == '提交'（去掉零宽字符），不能包含"查看提交记录"
9. **批量同内容工单必须逐单填提！** — 不能连填多单再批量提交。飞书表单提交后页面刷新，后续填写会覆盖前面的。正确做法：填 → 验证 → 提交 → 再填下一单。每个工单循环独立的填-验-提流程

---

## 表单字段索引（15 items，2026-05-21飞书更新）

| 索引 | 字段 | 填写方式 |
|------|------|----------|
| 0 | 报修人 | 点击 → 搜索框输入名字/账号 → 选第一个匹配的 |
| 1 | 接单人 | 自动生成，不管 |
| 2 | 办公区 | 自动生成，不管 |
| 3 | 一级分类 | 点击 → 等2秒 → 搜索 → 选匹配的 |
| 4 | 二级分类 | 点击 → 等2秒 → 搜索 → 选匹配的（用关键词子串匹配） |
| 5 | 问题现象 | contenteditable，无换行用`fill()`，有换行用`Shift+Enter`逐行输入 |
| 6 | 问题原因 | contenteditable，同上 |
| 7 | 处理步骤 | contenteditable，**必须用`Shift+Enter`方案**：逐行type + Shift+Enter换行，最后触发InputEvent |
| 8 | 接单时间 | 日期 `input[placeholder="年/月/日"]` fill + Enter，时间 `input[placeholder="时:分"]` fill + Enter |
| 9 | 关单时间 | 同上 |
| 10 | 处理时长 | 自动计算 |
| 11 | 工单填写规范 | 自动计算，不管 |
| 12 | 生产影响类 | 自动计算，不管（2026-05-21新增） |
| 13 | 引发率工单 | 自动计算，不管（2026-05-21新增） |
| 14 | 提交按钮 | 遍历button精确匹配`text == '提交'`，不能用`button:has-text("提交")` |

---

## 常见工单分类

### 安全软件类
- 一级分类：安全软件
- 二级分类：DLP、准入软件、Eset、个人设备入网/退网

### 不能体现工单类
- 一级分类：不能体现工单
- 二级分类：批量设备安装&更换&回收、其它不能体现工单、巡检类-WIFI测试、新入职&批量电脑配置等
- **注意**：不能体现工单类的报修人永远用金政龙（zhenglong.jin）

### 硬件支持类
- 一级分类：硬件支持
- 二级分类：电脑申请&配置、更换电脑、电脑硬件问题、显示器问题、转岗&硬件迁移、话机/耳机问题等
- **注意**：申请配置电脑（含账号、邮箱、打印机等）归到 硬件支持/电脑申请&配置，不是不能体现工单

### 邮件系统类
- 一级分类：邮件系统
- 二级分类：邮箱账号密码弹窗、邮件客户端问题、邮件清理&存档&扩容、配置电脑端邮箱等
- **注意**：邮箱账号密码弹窗+账号锁定类归到这里，不是账号密码/账户解锁

### 账号密码类
- 一级分类：账号密码
- 二级分类：Token PIN码问题、密码修改/重置、账户解锁

### WIFI测试工单（固定模板）
- 报修人：zhenglong.jin
- 一级分类：不能体现工单
- 二级分类：**搜索词用"WIFI测试"**（不能用全角破折号"巡检类—WIFI测试"）
- 问题现象：每日wifi巡检
- 问题原因：处于公司网络连通性和网速测试的需要
- 处理步骤：
  1.进行20F，22F，23Fwifi连通性和网速测试
  2.填写wifi表

---

## 调试技巧

- 填写完后截图在脚本目录下的 `screenshot_form.png`
- 填写日志在脚本目录下的 `fill_result_YYYYMMDD_HHMMSS.txt`（最新的就是刚填的）
- 提交结果在脚本目录下的 `fill_result.txt`
- 如果报修人搜不到，检查搜索词是否正确，尝试用中文名搜索
- 如果分类搜不到，检查分类名称关键词是否匹配
- 如果处理步骤没换行，检查 workorder_lib.py 是否用了 `Shift+Enter` 方案（见上面"处理步骤换行"说明）

### 验证结果与页面不一致时排查步骤

当结果文件显示 FAIL 但实际页面填写正确时，按以下步骤排查：

1. **直接连 CDP 抓页面 innerText**：写一个简单的 Playwright 脚本，`connect_over_cdp` 后逐个 item 打印 `inner_text()` + `repr()` 显示原始内容
2. **逐行检查过滤条件**：把 innerText 按 `\n` 分割，逐行对照过滤条件看哪行被误杀/漏过
3. **重点检查特殊字符**：`*`（必填标记）、零宽字符 `\u200b`、标签行（报修人/接单人/一级分类等）是否被正确排除
4. **不要盲目相信验证结果**：验证代码的 innerText 解析是脆弱的，出问题优先用第1步确认页面真实状态

**已知陷阱**：
- 报修人 Item[0] 的 innerText 包含 `*`（必填标记），过滤时必须加 `l.strip() != '*'`
- 分类 Item[3][4] 的 innerText 包含所有下拉选项，取第一行即为选中值
- contenteditable 的 innerText 换行是 `\n`，比较时两边都 `replace('\n', '')` 即可

---

## 依赖与运行环境

### 必需技能

| 技能 | 用途 |
|------|------|
| `agent-browser` | 通过 Playwright CDP 连接浏览器，操作表单元素 |

### Python 依赖

脚本需要 Python 3.10+ 和以下包：

```bash
pip install playwright
# 安装后还需要安装浏览器：
python -m playwright install chromium
```

### 运行环境要求

1. **Edge 浏览器已开启远程调试**：以 `--remote-debugging-port=9222` 参数启动
2. **飞书工单表单页面已在 Edge 中打开**：`https://hf7l9aiqzx.feishu.cn/share/base/form/shrcnPUG5g6KadooPDUqs31tGLz`
3. **正确的 Python 环境**（辰哥本机用 venv：`D:/Users/chenit.liang/.workbuddy/binaries/python/envs/default/Scripts/python.exe`）

### 脚本调用关系

```
fill_form.py  ───→  workorder_lib.py  ───→  Playwright CDP (Edge 9222)
submit_form.py ───→  workorder_lib.py  ───→  同上
```

> ⚠️ workorder_lib.py 是核心库，fill_form 和 submit_form 都依赖它。**禁止修改 workorder_lib.py 的核心逻辑！**
