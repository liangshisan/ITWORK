---
name: asset-barcode
description: 资产条形码识别与出入库记录生成。当用户发送设备资产条形码图片、要求识别资产编号并生成出入库表格数据时使用。支持 QITDP（显示器）、QITNB（笔记本）、QITPC（台式机）三种前缀自动分类，支持入库（填写到「入库记录」sheet）和出库（填写到「出库记录」sheet）两种记录。
agent_created: true
---

# 资产条形码识别出入库

识别设备资产条形码图片中的资产编号，自动分类并生成出入库记录，填写到金山文档在线表。

## 触发条件

- 用户发送条形码/资产标签图片，要求识别资产编号
- 用户说"识别条形码""资产入库/出库""帮我录入"等
- 用户连续发多张图片后说"发完了"，再统一输出结果

## 核心规则

### 判断入库还是出库

- 用户明确说**入库**或**出库** → 按用户说的来
- 用户没说 → **必须问清楚再动手**
- 同一批数据必须是同一种（不要混合）

### 资产编号前缀 → 设备类别映射

| 前缀 | D列 设备类别 | E列 具体描述 |
|------|------------|------------|
| QITDP | `显示器` | `23寸显示器` |
| QITNB | `笔记本` | `技术本` |
| QITPC | `台式机` | `品牌台式机` |

**⚠️ D 列（设备类别）必须和在线表下拉选项完全一致：只能填 `显示器`/`笔记本`/`台式机` 三者之一，填别的全落空！**

**⚠️ E 列（具体描述）规则：三个前缀各填各的，不要所有设备都填"技术本"！**

### 默认值

- 地区：成都
- **入库默认类型：一人多机归还**
- **出库默认类型：IT工作台申请**
- 日期：当天日期（格式 YYYY/M/D，不补零）
- 账号列留空

### 入库可选类型

离职入库、借用归还、部门公用归还、设备更换、一人多机归还、调拨入库

### 出库可选类型

新人入职、部门公用、外包使用、设备更换、IT工作台申请、调拨出库

---

## 填写入口：asset_fill.py v4

**脚本位置：技能目录下的 `asset_fill.py`（和本 SKILL.md 在同一个文件夹里）**
**辰哥本机：`D:\Users\chenit.liang\WorkBuddy\Claw\.workbuddy\asset_fill.py`（远端同步入口）**

用法：
```bash
python asset_fill.py --mode=入库 --data='[["成都","一人多机归还","2026/6/29","笔记本","技术本","QITNB021521","hongshi.yang"]]'
python asset_fill.py --mode=出库 --data='[["成都","IT工作台申请","2026/6/29","显示器","23寸显示器","QITDP003311","hexuan.li"]]'
```

**核心5步（脚本自动完成）：**
1. `page.reload()` 清筛选器
2. TreeWalker 精确点击 sheet tab 切换
3. B2 验证（不通过 → 重试 → FATAL 退出）
4. Ctrl+A×2+C 全选 → 内存扫描找空行 → ArrowDown 导航
5. F2/Ctrl+A/Delete/type/Ctrl+Enter 逐格填入 → Ctrl+A+C 验证

**如果 asset_fill.py 失败，回退用直连方式**：Ctrl+Home → ArrowDown×(行号-1) → F2逐格填写 → Ctrl+Enter。

---

## 执行流程

### 第1步：识别条形码（只识别资产编号）

收到图片后，加载 `video-image-file-analysis` 技能识别。

**⚠️ 只提取资产编号！** 不管入库还是出库，识别结果只输出资产编号（如 QITDP011650）。不需要识别品牌型号、序列号、购置日期等额外信息。

识别输出格式（一行一条）：
```
QITDP011650
QITNB018007
```

### 第2步：生成记录 + 展示格式确认

从资产编号前缀自动判断设备类别和具体描述，按默认值生成记录。

以 markdown 表格格式输出（6列）：

```markdown
| 地区 | 类型 | 日期 | 设备类别 | 具体描述 | 资产编号 |
|------|------|------|---------|---------|---------|
| 成都 | 一人多机归还 | 2026/6/8 | 显示器 | 23寸显示器 | QITDP005009 |
```

**格式规则：** 日期 YYYY/M/D（不补零）、表格前后不加额外列。

#### ⚠️ 出库前必查历史格式（辰哥强调，2026-06-25）

填写之前必须先读同前缀历史记录，展示 E 列格式给辰哥确认！不要自己瞎猜。

流程：全选读在线表数据 → 找同前缀最近几条 → 展示 D列+E列 → 辰哥确认 → 再填写。

### 第3步：去 ITDB 查询 QTALK ID（仅入库）

**入库时必须先到 ITDB 查使用人（QTALK ID），填写到在线表的 I 列！**

ITDB 地址：`http://itdb.corp.qunar.com/asset_manager/asset_manager`

```python
# 查询流程（这段不在 asset_fill.py 里，单独执行）
await page.fill('input[placeholder*="请输入资产编号"]', asset_id)
await page.click('button:has-text("查询")')
await asyncio.sleep(3)
cells = await page.locator('.table tbody tr:has-text("'+asset_id+'") td').all()
qtalk_id = (await cells[5].inner_text()).strip()  # 使用人 = QTALK ID
```

### 第4步：填写到金山文档在线表

金山文档地址：`https://www.kdocs.cn/l/cjOHzkzNul1x`

- **入库** → 「**入库记录**」sheet
- **出库** → 「**出库记录**」sheet

**⚠️ 同一个金山文档有多个 sheet，入库和出库是分开的两个 sheet，绝对不能搞混！**

#### 表格列结构（A~I 列）

| 列 | 字段 | 填写内容 |
|------|------|---------|
| A | 地区 | 固定"成都" |
| B | 类型 | 入库/出库类型 |
| C | 日期 | YYYY/M/D |
| D | 设备类别 | 显示器/笔记本/台式机（必须精确！） |
| E | 具体描述 | 按前缀填（23寸显示器/技术本/品牌台式机） |
| F | 资产编号 | 如 QITDP005009 |
| G | SN | 留空 |
| H | 型号 | 留空 |
| I | 领用人/QTALK ID | 入库=ITDB查的QTALK ID，出库=用户给的领用人 |

**⚠️ 入库必须填 I 列（QTALK ID），出库必须填 I 列（领用人）。不能漏！**

#### Sheet 切换方式

金山文档 Canvas 渲染下，**必须用 `mouse.click` 坐标点击 sheet tab**，禁止操作 DOM class。

切换后必须验证 B2 单元格：
- B2 = "入库原因" → 入库表 ✓
- B2 = "出库原因" → 出库表 ✓

**⚠️ 读 B2 绝对不要按 F2！** 直接选中 B2 后 `Ctrl+C` 读剪贴板。F2 进编辑模式会触发状态恢复导致 sheet 切回默认页。

### 第5步：验证 + 本地备份

填写完成后**必须验证**：
1. Ctrl+A 全选 → Ctrl+C 复制 → 读剪贴板 TSV
2. 按行号定位目标行，逐列比对
3. **全部 OK 才算通过**，有一列不匹配就修复
4. 验证结果展示给辰哥确认

**本地备份**：验证通过的 TSV 写入 `D:\SendToChen\出入库.xlsx` 对应 sheet。

---

## ⚠️ 重要注意事项

### 关键操作规则

1. **导航用箭头键，不用 F5/Ctrl+G**：F5/Ctrl+G 跳转不可靠，会填错单元格
2. **填写用 Ctrl+Enter 确认**：普通 Enter 会让焦点移到下一行，Ctrl+Enter 焦点不动
3. **找空行用全选复制法**：Ctrl+A → Ctrl+C → 读剪贴板 → `split("\n")` → 内存扫描空行
4. **先备份再填写**：全选复制 → 写本地 Excel 备份 → 再开始填在线表
5. **禁止发送 Ctrl+Shift+L**：金山文档 Web 版此快捷键激活筛选器而非清除，会导致 Ctrl+A 只选可见行
6. **禁止操作 sheet tab 的 DOM class**：手动 `classList.add/remove('selected')` 会污染框架状态

### 入库流程（完整）

1. 识别资产编号 → 判断前缀
2. 生成记录（markdown 表格展示）→ 等辰哥确认
3. 去 ITDB 逐个查 QTALK ID
4. 打开金山文档 → 切换「入库记录」sheet → B2 验证
5. 全选备份 → 找空行 → 逐格填写 A~I 列
6. 全选验证 → 本地 Excel 备份 → 展示结果

### 出库流程（完整）

1. 识别资产编号 → 判断前缀
2. **先读同前缀历史记录**，展示 E 列格式 → 等辰哥确认
3. 生成记录（markdown 表格展示）
4. 打开金山文档 → 切换「出库记录」sheet → B2 验证
5. 全选备份 → 找空行 → 逐格填写 A~I 列（领用人直接在记录里）
6. 全选验证 → 本地 Excel 备份 → 展示结果

### 验证不可跳过

填写完成后必须用整行复制法逐列验证。如果验证失败：
- 不要说"填好了"
- 把实际页面内容展示给辰哥
- 说明哪列填错了，正在修复

### 日期格式

- 在线表填：`YYYY/M/D`（如 `2026/6/9`，不补零）
- 本地 Excel 自动格式化

---

## 依赖与运行环境

### 必需技能

| 技能 | 用途 |
|------|------|
| `video-image-file-analysis` | 识别条形码图片中的资产编号 |
| `agent-browser` | 通过 Playwright CDP 操作金山文档在线表 |

### Python 依赖

脚本需要 Python 3.10+ 和以下包：

```bash
pip install playwright
# 安装后还需要安装浏览器：
python -m playwright install chromium
```

### 运行环境要求

1. **Edge 浏览器已开启远程调试**：以 `--remote-debugging-port=9222` 参数启动
2. **金山文档出入库表已在 Edge 中打开**：`https://www.kdocs.cn/l/cjOHzkzNul1x`
3. **入库时需可访问 ITDB**：`http://itdb.corp.qunar.com/asset_manager/asset_manager`（内网）
4. **本地备份路径**：`D:\SendToChen\出入库.xlsx`（辰哥本机专属，他人可改）

### 脚本说明

```
asset_fill.py ───→ Playwright CDP (Edge 9222) ───→ 金山文档在线表
```

> ITDB 查询代码不在 asset_fill.py 中，需单独执行（见执行流程第3步）。
