"""
QSSO 自动登录 — 复用已打开的 QSSO 页面，通过浏览器扩展获取 TOTP 并提交。
用法:
  python qss_login.py                    # 默认登录 ITworkstation
  python qss_login.py --ret URL         # 指定 redirect URL
"""
import re
import time
import sys
import argparse

PIN = '123456'
USERNAME = 'chenit.liang'
TOTP_PERIOD = 30
MIN_REMAINING = 10  # 至少剩 10 秒才敢填
EXT_POPUP = 'chrome-extension://bhghoamapcdpbohphigoooaddinpkbai/view/popup.html'
DEFAULT_RET = (
    'https://qsso.corp.qunar.com/login.php?ret='
    'https%3A%2F%2Fit.corp.qunar.com%2Fitworkstation%2Fit%2Flogin'
    '%3Fbreakurl%3DL2l0d29ya3N0YXRpb24vaXQvSVREZXZpY2VzTWFpbnBhZ2UuaHRtbA%3D%3D'
)


def otp_remaining():
    return TOTP_PERIOD - (int(time.time()) % TOTP_PERIOD)


def main():
    parser = argparse.ArgumentParser(description='QSSO 自动登录')
    parser.add_argument('--ret', default=DEFAULT_RET, help='QSSO redirect URL')
    parser.add_argument('--check-only', action='store_true', help='仅获取 OTP，不登录')
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')

        # 1. Find existing QSSO page (reuse, don't open new)
        qsso_page = None
        for pg in browser.contexts[0].pages:
            if 'qsso.corp.qunar.com/login' in pg.url:
                qsso_page = pg
                break

        if not qsso_page:
            print('❌ 未找到已打开的 QSSO 页面，请先在 Edge 打开 qsso.corp.qunar.com')
            browser.close()
            sys.exit(1)

        print(f'[复用页面] 已找到 QSSO 登录页')

        # 2. Check OTP timing — wait if too close to refresh
        rem = otp_remaining()
        print(f'[时效检查] 距下次刷新: {rem}s')
        if rem < MIN_REMAINING:
            wait = rem + 2
            print(f'[等待] 剩余 {rem}s 不够，等 {wait}s 到下一轮…')
            time.sleep(wait)
            rem = otp_remaining()
            print(f'[等待完成] 新周期开始，剩余 ~{rem}s')

        # 3. Get OTP from browser extension
        otp_pg = browser.contexts[0].new_page()
        otp_pg.goto(EXT_POPUP, timeout=5000)
        otp_pg.wait_for_timeout(500)
        text = otp_pg.evaluate('() => document.body.innerText')
        otp_code = re.findall(r'\b\d{6}\b', text)[0]
        otp_pg.close()
        rem = otp_remaining()
        print(f'[OTP] {otp_code}（剩余 {rem}s）')

        if args.check_only:
            print(f'[OTP] {otp_code}')
            browser.close()
            return

        # 4. Fill form and submit
        qsso_page.bring_to_front()
        qsso_page.locator('input#userId').fill(USERNAME)
        passcode = PIN + otp_code
        qsso_page.locator('input#passCode').fill(passcode)
        print(f'[提交] passcode={passcode}（提交时剩余 {otp_remaining()}s）')
        qsso_page.locator('input#signIn').click()

        # 5. Wait for redirect & verify
        qsso_page.wait_for_timeout(5000)
        print(f'[结果] {qsso_page.url[:80]}')
        print(f'[结果] 标题: {qsso_page.title()}')

        if 'it.corp.qunar' in qsso_page.url:
            print('✅ QSSO 登录成功！')
        else:
            print('⚠️ 登录可能失败，请检查页面')
            browser.close()
            sys.exit(1)

        browser.close()


if __name__ == '__main__':
    main()
