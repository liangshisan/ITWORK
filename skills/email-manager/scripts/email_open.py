"""
邮箱开通模块 - 通过 Playwright CDP 连接 Edge 操控邮箱开通页面
用法: python email_open.py <account>
前置条件: Edge 浏览器已登录 QSSO（有 it.corp.qunar.com 的登录态）
"""
import sys
from playwright.sync_api import sync_playwright

EMAIL_PAGE_URL = 'https://it.corp.qunar.com/itworkstation/it/open_email.html'
CDP_URL = 'http://127.0.0.1:9222'


def open_email(account: str, screenshot_path: str = 'email_page.png'):
    """
    在邮箱开通页面输入账号并提交
    使用已有 Edge 标签页（保留登录态），不新建标签页
    """
    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp(CDP_URL)
    
    # 使用第一个已有标签页导航（保留 SSO 登录态）
    pages = browser.contexts[0].pages
    if not pages:
        raise RuntimeError('Edge 浏览器无可用标签页')
    
    page = pages[0]
    page.goto(EMAIL_PAGE_URL, timeout=30000)
    page.wait_for_load_state('networkidle')
    
    # 检查是否跳转到了 QSSO 登录页
    if 'qsso.corp.qunar.com' in page.url:
        raise RuntimeError('跳转到 QSSO 登录页，请先在 Edge 中登录后再试')
    
    print(f'Page loaded: {page.url}')
    
    # 填写 Qtalk 账号
    inp = page.locator('input[type=text]').first
    inp.click()
    inp.fill(account)
    print(f'Filled: {account}')
    
    # 点击提交按钮
    btn = page.locator('button:has-text("提交")')
    if btn.count() == 0:
        # fallback: 列出所有按钮帮助排查
        buttons = page.locator('button')
        for i in range(buttons.count()):
            b = buttons.nth(i)
            print(f'  btn[{i}]: [{b.text_content().strip()}]')
        raise RuntimeError('未找到提交按钮')
    
    btn.click()
    print('Submit clicked, waiting...')
    page.wait_for_timeout(3000)
    
    # 截图保存结果
    page.screenshot(path=screenshot_path, full_page=True)
    print(f'Done. Screenshot: {screenshot_path}')
    
    p.stop()
    return screenshot_path


if __name__ == '__main__':
    account = sys.argv[1] if len(sys.argv) > 1 else 'wenyuan.chen'
    open_email(account)
