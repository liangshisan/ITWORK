"""
工单填写通用函数 — 不要修改此文件！
每次提工单只改 fill_form.py 里的参数，不要动这里的逻辑。
"""
import asyncio
import os
import time
from playwright.async_api import async_playwright

# 工单表单 URL — 优先从环境变量 WORKORDER_FORM_URL 读取，否则用默认值
# 首次使用请设置: set WORKORDER_FORM_URL=你的工单表单URL
FORM_URL = os.environ.get("WORKORDER_FORM_URL",
    "https://hf7l9aiqzx.feishu.cn/share/base/form/shrcnPUG5g6KadooPDUqs31tGLz")

async def fill_work_order(
    reporter_search: str,       # 报修人搜索关键词（账号）
    reporter_match: str = None, # 报修人匹配文字（不填则取第一个结果）
    category1: str = None,      # 一级分类
    category2: str = None,      # 二级分类
    phenomenon: str = "",       # 问题现象（不少于5字符）
    cause: str = "",            # 问题原因（不少于5字符）
    steps: str = "",            # 处理步骤（不少于10字符，用\n分行）
    accept_date: str = "",      # 接单日期 YYYY/MM/DD
    accept_time: str = "",      # 接单时间 HH:MM
    close_date: str = "",       # 关单日期
    close_time: str = "",       # 关单时间
):
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]

        target_page = None
        for pg in context.pages:
            if "feishu" in pg.url and "form" in pg.url:
                target_page = pg
                break
        if not target_page:
            target_page = await context.new_page()

        await target_page.goto(FORM_URL, wait_until="networkidle", timeout=30000)
        await target_page.wait_for_timeout(1000)
        items = await target_page.query_selector_all(".ud__form__item")
        log = [f"items: {len(items)}"]

        # --- 报修人 ---
        # 修复：click 可能被 modal 拦截导致超时，使用 force=True 并确保 modal 出现
        await items[0].click(force=True, timeout=2000)
        await target_page.wait_for_timeout(1000)
        # 搜索框在弹出的 modal 内，不在 items[0] 内，改为全局查找
        search_input = await target_page.query_selector('.bitable-selector-user-modal input[placeholder="搜索成员"]')
        if not search_input:
            search_input = await target_page.query_selector('input[placeholder="搜索成员"]')
        await search_input.fill(reporter_search)
        await target_page.wait_for_timeout(1500)
        opts = await target_page.query_selector_all('.b-user-select-item-name')
        match_key = reporter_match or reporter_search.lower()
        clicked = False
        for opt in opts:
            text = (await opt.inner_text()).replace('\u200b', '').strip()
            if match_key in text or match_key in text.lower():
                await opt.click()
                log.append(f"报修人: {text}")
                clicked = True
                break
        if not clicked and opts:
            text = (await opts[0].inner_text()).replace('\u200b', '').strip()
            await opts[0].click()
            log.append(f"报修人: {text}")
        # 关闭报修人下拉
        await target_page.mouse.click(10, 200)
        await target_page.wait_for_timeout(500)

        # --- 一级分类 ---
        if category1:
            await items[3].click()
            await target_page.wait_for_timeout(2000)
            s1 = await items[3].query_selector('input[placeholder="查找选项"]')
            if not s1:
                s1 = await target_page.query_selector('input[placeholder="查找选项"]')
            if s1:
                await s1.fill(category1)
                await target_page.wait_for_timeout(1000)
                clicked = False
                for opt in await target_page.query_selector_all('.b-select-option'):
                    text = (await opt.inner_text()).replace('\u200b', '').strip()
                    cls = await opt.get_attribute('class') or ''
                    if category1 in text and 'disabled' not in cls:
                        await opt.click()
                        log.append(f"一级分类: {text}")
                        clicked = True
                        break
                if not clicked:
                    all_opts = await target_page.query_selector_all('.b-select-option')
                    opt_texts = []
                    for opt in all_opts:
                        t = (await opt.inner_text()).replace('\u200b', '').strip()
                        opt_texts.append(t[:30])
                    log.append(f"一级分类未匹配, 选项: {opt_texts[:5]}")
            else:
                log.append("一级分类搜索框未找到")
            await target_page.mouse.click(10, 200)
            await target_page.wait_for_timeout(500)

        # --- 二级分类 ---
        if category2:
            await items[4].click()
            await target_page.wait_for_timeout(2000)
            s2 = await items[4].query_selector('input[placeholder="查找选项"]')
            if not s2:
                s2 = await target_page.query_selector('input[placeholder="查找选项"]')
            if s2:
                await s2.fill(category2)
                await target_page.wait_for_timeout(1000)
                clicked = False
                for opt in await target_page.query_selector_all('.b-select-option'):
                    text = (await opt.inner_text()).replace('\u200b', '').strip()
                    cls = await opt.get_attribute('class') or ''
                    if category2 in text and 'disabled' not in cls:
                        await opt.click()
                        log.append(f"二级分类: {text}")
                        clicked = True
                        break
                if not clicked:
                    all_opts = await target_page.query_selector_all('.b-select-option')
                    opt_texts = []
                    for opt in all_opts:
                        t = (await opt.inner_text()).replace('\u200b', '').strip()
                        opt_texts.append(t[:30])
                    log.append(f"二级分类未匹配, 选项: {opt_texts[:5]}")
            else:
                log.append("二级分类搜索框未找到")
            await target_page.mouse.click(10, 200)
            await target_page.wait_for_timeout(500)

        # --- 文本字段 ---
        for idx, name, content in [(5, "问题现象", phenomenon), (6, "问题原因", cause), (7, "处理步骤", steps)]:
            if content:
                # 处理分隔符：支持字面 \n 或 ||| 做换行标记
                content = content.replace('\\n', '\n').replace('|||', '\n')
                await items[idx].click()
                await target_page.wait_for_timeout(300)
                ce = await items[idx].query_selector('[contenteditable="true"]')
                if not ce:
                    log.append(f"{name}: 未找到输入框")
                    continue
                if '\n' in content:
                    # 飞书编辑器：先清空，再逐行输入，用 Shift+Enter 换行
                    lines = content.split('\n')
                    await ce.click()
                    await target_page.wait_for_timeout(200)
                    # 全选并删除
                    await target_page.keyboard.press("Control+a")
                    await target_page.keyboard.press("Backspace")
                    await target_page.wait_for_timeout(200)
                    for i, line in enumerate(lines):
                        await target_page.keyboard.type(line)
                        if i < len(lines) - 1:
                            # 飞书编辑器用 Shift+Enter 软换行
                            await target_page.keyboard.press("Shift+Enter")
                            await target_page.wait_for_timeout(150)
                    # 触发 input 事件
                    await ce.evaluate('(el) => { el.dispatchEvent(new InputEvent("input", {bubbles:true})); }')
                    await target_page.wait_for_timeout(300)
                else:
                    await ce.fill(content)
                log.append(f"{name}: OK")

        # --- 接单时间 ---
        if accept_date or accept_time:
            await items[8].click()
            await target_page.wait_for_timeout(200)
            for inp in await items[8].query_selector_all('input[placeholder="年/月/日"]'):
                if accept_date:
                    await inp.click()
                    await inp.fill(accept_date)
                    await inp.press("Enter")
                    await target_page.wait_for_timeout(300)
            for inp in await items[8].query_selector_all('input[placeholder="时:分"]'):
                if accept_time:
                    await inp.click()
                    await inp.fill(accept_time)
                    await inp.press("Enter")
                    await target_page.wait_for_timeout(300)
            log.append(f"接单时间: {accept_date} {accept_time}")

        # --- 关单时间 ---
        if close_date or close_time:
            await items[9].click()
            await target_page.wait_for_timeout(200)
            for inp in await items[9].query_selector_all('input[placeholder="年/月/日"]'):
                if close_date:
                    await inp.click()
                    await inp.fill(close_date)
                    await inp.press("Enter")
                    await target_page.wait_for_timeout(300)
            for inp in await items[9].query_selector_all('input[placeholder="时:分"]'):
                if close_time:
                    await inp.click()
                    await inp.fill(close_time)
                    await inp.press("Enter")
                    await target_page.wait_for_timeout(300)
            log.append(f"关单时间: {close_date} {close_time}")

        await target_page.mouse.click(10, 200)
        await target_page.wait_for_timeout(500)

        # --- 验证：逐字段读取页面实际值 ---
        log.append("=== 验证 ===")
        items_v = await target_page.query_selector_all(".ud__form__item")
        checks = []
        
        # 报修人：从 innerText 提取（排除标签、必填标记*、接单人）
        reporter_text = (await items_v[0].inner_text()).replace('\u200b', '').strip()
        reporter_lines = [
            l for l in reporter_text.split('\n')
            if l.strip() and l.strip() != '*' and '报修人' not in l and '接单人' not in l
        ]
        actual_reporter = reporter_lines[0] if reporter_lines else ''
        checks.append(("报修人", reporter_search, actual_reporter))
        
        # 一级分类：从 innerText 提取
        c1_text = (await items_v[3].inner_text()).replace('\u200b', '').strip()
        c1_lines = [l for l in c1_text.split('\n') if l.strip() and '一级分类' not in l and '*' not in l]
        actual_c1 = c1_lines[0] if c1_lines else ''
        checks.append(("一级分类", category1 or "", actual_c1))
        
        # 二级分类
        c2_text = (await items_v[4].inner_text()).replace('\u200b', '').strip()
        c2_lines = [l for l in c2_text.split('\n') if l.strip() and '二级分类' not in l and '*' not in l]
        actual_c2 = c2_lines[0] if c2_lines else ''
        checks.append(("二级分类", category2 or "", actual_c2))
        
        # 文本字段：用 innerText 保留换行
        for idx, name, expected in [(5,"问题现象",phenomenon),(6,"问题原因",cause),(7,"处理步骤",steps)]:
            ce = await items_v[idx].query_selector('[contenteditable="true"]')
            actual = (await ce.inner_text()).replace('\u200b', '').strip() if ce else ''
            checks.append((name, expected or "", actual))
        
        # 时间字段
        d1 = await items_v[8].query_selector('input[placeholder="年/月/日"]')
        t1 = await items_v[8].query_selector('input[placeholder="时:分"]')
        actual_accept = f"{await d1.input_value() if d1 else ''} {await t1.input_value() if t1 else ''}".strip()
        checks.append(("接单时间", f"{accept_date} {accept_time}".strip(), actual_accept))
        
        d2 = await items_v[9].query_selector('input[placeholder="年/月/日"]')
        t2 = await items_v[9].query_selector('input[placeholder="时:分"]')
        actual_close = f"{await d2.input_value() if d2 else ''} {await t2.input_value() if t2 else ''}".strip()
        checks.append(("关单时间", f"{close_date} {close_time}".strip(), actual_close))
        
        for name, expected, actual in checks:
            # 比较：去掉换行差异后对比
            exp_clean = expected.replace('\n', '')
            act_clean = actual.replace('\n', '')
            status = "PASS" if act_clean and (exp_clean in act_clean or act_clean in exp_clean) else "FAIL"
            log.append(f"[{name}] 预期:{expected} | 实际:{actual} | {status}")

        screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshot_form.png")
        await target_page.screenshot(path=screenshot_path)

        ts = time.strftime("%Y%m%d_%H%M%S")
        result_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"fill_result_{ts}.txt")
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log))
        return log
