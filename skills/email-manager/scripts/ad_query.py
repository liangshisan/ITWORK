"""
AD 查询模块 - 通过 pyautogui 操控 AD 查询工具
用法: python ad_query.py <account>
输出: 截图保存到 CWD 的 ad_query_result.png，打印关键信息到 stdout
"""
import ctypes, time, os, sys
import pyautogui

user32 = ctypes.windll.user32

class RECT(ctypes.Structure):
    _fields_ = [('l', ctypes.c_long), ('t', ctypes.c_long),
                ('r', ctypes.c_long), ('b', ctypes.c_long)]

def find_window(title_part: str):
    """查找窗口句柄"""
    r = []
    def cb(h, _):
        l = user32.GetWindowTextLengthW(h)
        if l > 0:
            b = ctypes.create_unicode_buffer(l + 1)
            user32.GetWindowTextW(h, b, l + 1)
            if title_part in b.value:
                r.append(h)
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_long)
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return r

def query_ad(account: str, screenshot_path: str = 'ad_query_result.png'):
    """
    在 AD 查询工具中查询指定账号
    前置条件: 剪贴板已由 PowerShell Set-Clipboard 设置为账号内容
    """
    # 找到窗口
    windows = find_window('AD')
    if not windows:
        raise RuntimeError('AD 查询工具未运行，请先启动')
    
    hwnd = windows[0]
    r = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    wl, wt = r.l, r.t
    
    # 激活窗口
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    
    # 全屏校准坐标（窗口最大化 0,0-1920,1200）
    INPUT_X, INPUT_Y   = 166, 149   # 用户登录名输入框
    BTN_X,   BTN_Y     = 382, 145   # 查询按钮
    CB_X,    CB_Y      = 553, 153   # 查询邮箱相关属性复选框（+4px补偿箭头尖→中心）
    
    # 1. 点击输入框 → Ctrl+A → Ctrl+V
    pyautogui.click(wl + INPUT_X, wt + INPUT_Y)
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.15)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.4)
    print(f'Pasted: {account}')
    
    # 2. 点击邮箱复选框
    pyautogui.click(wl + CB_X, wt + CB_Y)
    time.sleep(0.3)
    
    # 3. 点击查询按钮
    pyautogui.click(wl + BTN_X, wt + BTN_Y)
    print(f'Querying... wait 12s')
    time.sleep(12)
    
    # 4. 截图
    img = pyautogui.screenshot(region=(wl, wt, r.r - wl, r.b - wt))
    img.save(screenshot_path)
    print(f'Query complete. Screenshot: {screenshot_path}')
    return screenshot_path


if __name__ == '__main__':
    account = sys.argv[1] if len(sys.argv) > 1 else 'wenyuan.chen'
    query_ad(account)
