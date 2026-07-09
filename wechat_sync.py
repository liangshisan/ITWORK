"""
微信消息自动同步工具 — 桌面端 ↔ 微信双端无缝同步
==============================================
用法:
  # 启动后台守护进程（开机自启或手动启动）
  python wechat_sync.py daemon

  # 推送一条消息到微信（桌面端回复时调用）
  python wechat_sync.py push "消息内容"

  # 查看运行状态
  python wechat_sync.py status

  # 停止守护进程
  python wechat_sync.py stop

原理:
  daemon 进程在后台长轮询微信消息，自动缓存 context_token。
  当 push 命令写入队列文件时，daemon 立即用最新 token 推送到微信。
  Token 过期时自动等待下一条微信消息刷新。
"""
import requests
import json
import random
import time
import sys
import os
import threading

# ── 配置 ──────────────────────────────────────
BOT_TOKEN = '42c0727e3308@im.bot:0600001bbe7dd8e2e4bb62004f273a87d980ad'
BASE_URL = 'https://ilinkai.weixin.qq.com'
TO_USER = 'o9cq8008PapR6yLIMxZX4C_68BFE@im.wechat'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, '.wechat_token.json')
OUTBOX_FILE = os.path.join(BASE_DIR, '.wechat_outbox.jsonl')
PID_FILE = os.path.join(BASE_DIR, '.wechat_sync.pid')
BASE_INFO = {'channel_version': '2.4.3', 'bot_agent': 'weixin-ClawBot-API/2.0 (python)'}


def _make_headers():
    return {
        'Content-Type': 'application/json',
        'AuthorizationType': 'ilink_bot_token',
        'iLink-App-Id': 'bot',
        'iLink-App-ClientVersion': '2.4.3',
        'Authorization': f'Bearer {BOT_TOKEN}',
        'X-WECHAT-UIN': f'{random.randint(0, 0xFFFFFFFF):08x}'
    }


# ── Token 管理 ────────────────────────────────
class TokenStore:
    """线程安全的 token 缓存"""

    def __init__(self):
        self.lock = threading.Lock()
        self.token = None
        self.from_id = None
        self.updated_at = 0
        self._load()

    def _load(self):
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                self.token = d.get('context_token')
                self.from_id = d.get('from_id', '')
                self.updated_at = d.get('updated_at', 0)
            except Exception:
                pass

    def _save(self):
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'context_token': self.token,
                'from_id': self.from_id or '',
                'to_user_id': TO_USER,
                'updated_at': self.updated_at
            }, f, ensure_ascii=False)

    def update(self, context_token, from_id=None):
        with self.lock:
            self.token = context_token
            self.from_id = from_id or ''
            self.updated_at = time.time()
            self._save()

    def get(self):
        with self.lock:
            if self.token is None:
                return None, None
            age = time.time() - self.updated_at
            if age > 1800:
                return None, None  # 过期
            return self.token, self.from_id


# ── API 调用 ──────────────────────────────────
def poll_messages(timeout=35):
    """长轮询获取微信消息"""
    try:
        r = requests.post(
            f'{BASE_URL}/ilink/bot/getupdates',
            headers=_make_headers(),
            json={'base_info': BASE_INFO},
            timeout=timeout + 5
        )
        data = r.json()
        return data.get('msgs', [])
    except Exception as e:
        print(f'[Poll] 异常: {e}')
        return []


def send_to_wechat(text, context_token):
    """发送消息到微信"""
    try:
        r = requests.post(
            f'{BASE_URL}/ilink/bot/sendmessage',
            headers=_make_headers(),
            json={
                'msg': {
                    'from_user_id': '',
                    'to_user_id': TO_USER,
                    'client_id': f'openclaw-weixin-{random.randint(0, 0xFFFFFFFF):08x}',
                    'message_type': 2,
                    'message_state': 2,
                    'context_token': context_token,
                    'item_list': [{'type': 1, 'text_item': {'text': text}}]
                },
                'base_info': BASE_INFO
            },
            timeout=15
        )
        return r.status_code == 200
    except Exception as e:
        print(f'[Send] 异常: {e}')
        return False


# ── 守护进程 ──────────────────────────────────
def daemon_run():
    """后台守护进程主循环"""
    print(f'[Daemon] 启动 (PID={os.getpid()})')

    # 写入 PID 文件
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    store = TokenStore()
    running = True

    def poll_loop():
        nonlocal running
        while running:
            msgs = poll_messages(timeout=35)
            for m in msgs:
                ct = m.get('context_token', '')
                fid = m.get('from_user_id', '')
                text_items = [
                    i.get('text_item', {}).get('text', '')
                    for i in m.get('item_list', [])
                    if i.get('type') == 1
                ]
                text = ' '.join(text_items) if text_items else '[非文本消息]'
                print(f'[微信→] {text}')
                store.update(ct, fid)
                print(f'[Token] 已刷新')

    def outbox_loop():
        nonlocal running
        while running:
            time.sleep(1)
            if not os.path.exists(OUTBOX_FILE):
                continue
            try:
                with open(OUTBOX_FILE, 'r', encoding='utf-8') as f:
                    raw = f.read()
                if not raw.strip():
                    continue

                lines = raw.strip().split('\n')
                unsent = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        text = entry.get('text', '')
                        if not text:
                            continue
                        token, _ = store.get()
                        if token is None:
                            print(f'[Outbox] 无 token，消息排队等待: {text[:30]}...')
                            unsent.append(line)
                            continue
                        ok = send_to_wechat(text, token)
                        if ok:
                            print(f'[桌面→微信] 已发送: {text[:40]}...')
                        else:
                            print(f'[桌面→微信] 发送失败，保留重试')
                            unsent.append(line)
                    except json.JSONDecodeError:
                        print(f'[Outbox] 解析失败: {line[:50]}')

                # 写回未发送的消息；全部发完则清空文件
                if unsent:
                    with open(OUTBOX_FILE, 'w', encoding='utf-8') as f:
                        for line in unsent:
                            f.write(line + '\n')
                else:
                    open(OUTBOX_FILE, 'w').close()
            except Exception as e:
                print(f'[Outbox] 异常: {e}')

    t1 = threading.Thread(target=poll_loop, daemon=True)
    t2 = threading.Thread(target=outbox_loop, daemon=True)
    t1.start()
    t2.start()

    try:
        while t1.is_alive() or t2.is_alive():
            t1.join(1)
            t2.join(1)
    except KeyboardInterrupt:
        print('\n[Daemon] 收到停止信号')
        running = False

    print('[Daemon] 已停止')


def cmd_push(text):
    """推送消息到微信（写入队列文件）"""
    entry = json.dumps({'text': text, 'ts': time.time()}, ensure_ascii=False)
    with open(OUTBOX_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')
    print(f'[Push] 已加入队列: {text[:50]}{"..." if len(text) > 50 else ""}')


def cmd_status():
    """查看状态"""
    store = TokenStore()
    token, fid = store.get()
    daemon_running = os.path.exists(PID_FILE)
    queue_pending = 0
    if os.path.exists(OUTBOX_FILE):
        with open(OUTBOX_FILE, 'r', encoding='utf-8') as f:
            queue_pending = sum(1 for _ in f)

    print(f'守护进程: {"运行中 ✅" if daemon_running else "未运行 ❌"}')
    print(f'Token:     {"有效 ✅" if token else "过期/无 ❌"}')
    if token:
        print(f'来源:      {fid}')
        print(f'时效:      {int(time.time() - store.updated_at)}秒前')
    print(f'待发队列:   {queue_pending} 条')


def cmd_stop():
    """停止守护进程"""
    if not os.path.exists(PID_FILE):
        print('守护进程未运行')
        return
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        os.kill(pid, 9)
        os.remove(PID_FILE)
        print(f'[Stop] 已终止 PID={pid}')
    except Exception as e:
        print(f'[Stop] 失败: {e} — 请手动删除 {PID_FILE}')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == 'daemon':
        daemon_run()
    elif cmd == 'push':
        if len(sys.argv) < 3:
            print('用法: python wechat_sync.py push "消息"')
            return
        cmd_push(sys.argv[2])
    elif cmd == 'status':
        cmd_status()
    elif cmd == 'stop':
        cmd_stop()
    else:
        print(f'未知命令: {cmd}\n用法: daemon | push "msg" | status | stop')


if __name__ == '__main__':
    main()
