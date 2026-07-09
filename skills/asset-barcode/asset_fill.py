#!/usr/bin/env python3
"""
资产出入库填写脚本 v4 — 极简版
核心流程：reload → TreeWalker 切 sheet → B2 验证(FATAL) → 全选找空行 → 写入 → Ctrl+A+C 验证

用法：
  python asset_fill.py --mode=入库 --data='[["成都","一人多机归还","2026/6/29","笔记本","技术本","QITNB021521","hongshi.yang"]]'
  python asset_fill.py --mode=入库 --file=records.json
"""
import asyncio, json, sys, argparse
from playwright.async_api import async_playwright

CDP_URL = "http://127.0.0.1:9222"
KDOCS_URL = "https://www.kdocs.cn/l/cjOHzkzNul1x"

SHEET_TABS = {"入库": "入库记录", "出库": "出库记录"}
SLEEP = {"reload": 0.5, "tab": 1.0, "copy": 0.3, "f2": 0.08, "sel": 0.04, "type": 0.04, "enter": 0.12, "key": 0.03}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=["入库", "出库"])
    p.add_argument("--data", default=None)
    p.add_argument("--file", default=None)
    return p.parse_args()


def load_records(args):
    if args.file:
        return json.load(open(args.file, "r", encoding="utf-8"))
    if args.data:
        return json.loads(args.data)
    print("[FATAL] 需要 --data 或 --file")
    sys.exit(1)


async def ctrl_a_copy(page):
    for _ in range(2):
        await page.keyboard.press("Escape"); await asyncio.sleep(SLEEP["key"])
    await page.mouse.click(300, 200); await asyncio.sleep(0.2)
    await page.keyboard.press("Control+Home"); await asyncio.sleep(0.2)
    await page.keyboard.press("Control+A"); await asyncio.sleep(0.2)
    await page.keyboard.press("Control+A"); await asyncio.sleep(0.2)
    await page.keyboard.press("Control+C"); await asyncio.sleep(SLEEP["copy"] + 0.2)
    return (await page.evaluate("() => navigator.clipboard.readText()")).strip().split("\n")


async def click_tab(page, name):
    pos = await page.evaluate("""(n) => {
        let w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        while (w.nextNode()) {
            let t = w.currentNode.textContent.trim(), r = w.currentNode.parentElement.getBoundingClientRect();
            if (t === n && r.y > 500) return {x: r.x + r.width/2, y: r.y + r.height/2};
        }
        return null;
    }""", name)
    if pos:
        await page.mouse.click(pos['x'], pos['y'])
        await asyncio.sleep(SLEEP["tab"])
        return True
    return False


async def check_b2(page):
    for _ in range(2):
        await page.keyboard.press("Escape"); await asyncio.sleep(SLEEP["key"])
    await page.mouse.click(300, 200); await asyncio.sleep(0.2)
    await page.keyboard.press("Control+Home"); await asyncio.sleep(0.2)
    await page.keyboard.press("ArrowDown"); await page.keyboard.press("ArrowRight")
    await page.keyboard.press("Control+C"); await asyncio.sleep(SLEEP["copy"])
    return (await page.evaluate("() => navigator.clipboard.readText()")).strip()


def find_empty_row(lines):
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.split("\t")]
        if len(cells) >= 6 and not any(cells[:6]):
            return i + 1
    return len(lines) + 1


async def main():
    args = parse_args()
    records = load_records(args)
    sheet_tab = SHEET_TABS[args.mode]

    p = await async_playwright().start()
    browser = await p.chromium.connect_over_cdp(CDP_URL)

    # 找或打开页面
    page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if "kdocs.cn" in pg.url: page = pg; break
    if not page:
        page = await browser.contexts[0].new_page()
        await page.goto(KDOCS_URL)
        await asyncio.sleep(2)
    await page.bring_to_front()

    # Reload 清筛选器
    await page.reload()
    await page.wait_for_load_state("networkidle", timeout=10000)
    await asyncio.sleep(SLEEP["reload"])
    print("[RELOAD]")

    # 切 sheet + B2 验证
    if not await click_tab(page, sheet_tab):
        print(f"[FATAL] 找不到 {sheet_tab} tab")
        await p.stop(); sys.exit(1)

    b2 = await check_b2(page)
    print(f"B2=[{b2[:30]}]")
    if args.mode not in b2:
        # 重试
        await click_tab(page, sheet_tab)
        b2 = await check_b2(page)
        print(f"B2 retry=[{b2[:30]}]")
        if args.mode not in b2:
            print(f"[FATAL] B2={b2}, 预期={args.mode}")
            await p.stop(); sys.exit(1)

    # 全选找空行
    lines = await ctrl_a_copy(page)
    empty_row = find_empty_row(lines)
    print(f"[SCAN] {len(lines)}行 → Row {empty_row}")

    # 导航到空行 A 列
    for _ in range(2):
        await page.keyboard.press("Escape"); await asyncio.sleep(SLEEP["key"])
    await page.mouse.click(300, 200); await asyncio.sleep(0.2)
    await page.keyboard.press("Control+Home"); await asyncio.sleep(0.2)
    for _ in range(empty_row - 1):
        await page.keyboard.press("ArrowDown"); await asyncio.sleep(0.005)
    await asyncio.sleep(0.1)

    # 逐条写入
    col_targets = [0, 1, 2, 3, 4, 5, 8]
    for ri, rec in enumerate(records):
        cur_col = 0
        for ci, ct in enumerate(col_targets):
            for _ in range(ct - cur_col):
                await page.keyboard.press("ArrowRight"); await asyncio.sleep(0.01)
            cur_col = ct

            val = rec[ci] if ci < 6 else rec[6]
            await page.keyboard.press("F2"); await asyncio.sleep(SLEEP["f2"])
            await page.keyboard.press("Control+A"); await asyncio.sleep(SLEEP["sel"])
            await page.keyboard.press("Delete"); await asyncio.sleep(SLEEP["sel"])
            await page.keyboard.type(str(val)); await asyncio.sleep(SLEEP["type"])
            await page.keyboard.press("Control+Enter"); await asyncio.sleep(SLEEP["enter"])

        # 下一条：回 A 列
        if ri < len(records) - 1:
            await page.keyboard.press("ArrowDown"); await asyncio.sleep(0.01)
            for _ in range(8):
                await page.keyboard.press("ArrowLeft"); await asyncio.sleep(0.01)

    # 验证
    print("[VERIFY]", end=" ")
    lines2 = await ctrl_a_copy(page)
    text2 = "\n".join(lines2)

    ok = fail = 0
    for ri, rec in enumerate(records):
        asset_id = rec[5]
        if asset_id in text2:
            ok += 1
        else:
            fail += 1
            print(f"✗ {asset_id}", end=" ")
    print(f"→ {ok} OK" if fail == 0 else f"→ {ok} OK / {fail} FAIL")

    await p.stop()

if __name__ == "__main__":
    asyncio.run(main())
