import asyncio
import os
import argparse
from playwright.async_api import async_playwright

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

async def main(confirmed: bool):
    if not confirmed:
        msg = "⛔ 提交被拦截：缺少用户确认。必须收到用户明确说'提交'两个字后才能执行。\n"
        msg += "   请确认后再运行：python submit_form.py --confirm yes"
        result_path = os.path.join(SCRIPT_DIR, "fill_result.txt")
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(msg)
        print(msg)
        return

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        contexts = browser.contexts
        page = None
        for ctx in contexts:
            for pg in ctx.pages:
                if "feishu" in pg.url and "form" in pg.url:
                    page = pg
                    break
            if page:
                break
        if not page:
            page = await browser.contexts[0].new_page()
            await page.goto("https://hf7l9aiqzx.feishu.cn/share/base/form/shrcnPUG5g6KadooPDUqs31tGLz", wait_until="domcontentloaded")
            await asyncio.sleep(3)

        buttons = await page.query_selector_all('button')
        submit_btn = None
        for btn in buttons:
            text = (await btn.text_content() or '').replace('\u200b', '').strip()
            if text == '提交':
                submit_btn = btn
                break
        log = []
        if submit_btn:
            await submit_btn.click()
            log.append("Submit button clicked")
            await asyncio.sleep(2)
        else:
            log.append("ERROR: Submit button not found")
        
        body_text = (await page.inner_text('body') or '')[:200]
        if '提交成功' in body_text:
            log.append("RESULT: 提交成功")
        elif '请完善' in body_text or '不能为空' in body_text:
            log.append(f"RESULT: 提交失败，页面提示: {body_text[:100]}")
        else:
            log.append(f"RESULT: 未知状态，页面内容: {body_text}")
        
        output = "\n".join(log)
        result_path = os.path.join(SCRIPT_DIR, "fill_result.txt")
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(output.encode('gbk', errors='replace').decode('gbk'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", choices=["yes"], help="必须显式传入 --confirm yes 才能提交，防止自动提交")
    args = parser.parse_args()
    asyncio.run(main(confirmed=(args.confirm == "yes")))
