import asyncio
from playwright.async_api import async_playwright

async def main():
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
            with open(r"d:\Users\chenit.liang\WorkBuddy\Claw\fill_result.txt", "w", encoding="utf-8") as f:
                f.write("NO_PAGE")
            return

        # 直接点提交，不等弹窗
        items = await page.query_selector_all('.ud__form__item')
        log = [f"Items: {len(items)}"]
        for i, item in enumerate(items):
            text = (await item.text_content() or '').replace('\u200b', '').strip()
            if '提交' in text:
                await item.click()
                log.append(f"Submit clicked at index {i}")
                await asyncio.sleep(1)
                break
        
        # 验证提交结果
        body_text = (await page.inner_text('body') or '')[:200]
        if '提交成功' in body_text:
            log.append("RESULT: 提交成功")
        elif '请完善' in body_text or '不能为空' in body_text:
            log.append(f"RESULT: 提交失败，页面提示: {body_text[:100]}")
        else:
            log.append(f"RESULT: 未知状态，页面内容: {body_text}")
        
        output = "\n".join(log)
        with open(r"d:\Users\chenit.liang\WorkBuddy\Claw\fill_result.txt", "w", encoding="utf-8") as f:
            f.write(output)
        print(output.encode('gbk', errors='replace').decode('gbk'))

asyncio.run(main())
