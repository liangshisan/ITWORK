"""
微信消息转发工具 — 桌面端 → 微信
用法:
  python wechat_forward.py send "消息内容"        # 发消息到微信
  python wechat_forward.py listen                 # 长轮询监听新消息，刷新token
  python wechat_forward.py status                  # 查看 token 状态
"""
import requests
import json
import random
import time
import sys
import os

BOT_TOKEN = '42c0727e3308@im.bot:0600001bbe7dd8e2e4bb62004f273a87d980ad'
BASE_URL = 'https://ilinkai.weixin.qq.com'
TO_USER = 'o9cq8008PapR6yLIMxZX4C_68BFE@im.wechat'
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.wechat_token.json')

HEADERS = {
    'Content-Type': 'application/json',
    'AuthorizationType': 'ilink_bot_token',
    'iLink-App-Id': 'bot',
    'iLink-App-ClientVersion': '2.4.3',
    'X-WECHAT-UIN': '',  # 每次请求重新生成
}
BASE_INFO = {'channel_version': '2.4.3', 'bot_agent': 'weixin-ClawBot-API/1.0.1 (python)'}


def _make_headers():
    h = HEADERS.copy()
    h['Authorization'] = f'Bearer {BOT_TOKEN}'
    h['X-WECHAT-UIN'] = f'{random.randint(0, 0xFFFFFFFF):08x}'
    return h


def read_token():
    """读取缓存的 context_token，返回 (token, from_id, updated_at) 或 (None, None, 0)"""
    if not os.path.exists(TOKEN_FILE):
        return None, None, 0
    try:
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('context_token'), data.get('from_id'), data.get('updated_at', 0)
    except Exception:
        return None, None, 0


def save_token(context_token, from_id=None):
    """保存 context_token 到本地缓存"""
    data = {
        'context_token': context_token,
        'from_id': from_id or '',
        'to_user_id': TO_USER,
        'updated_at': time.time()
    }
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f'[Token] 已缓存 (from={from_id})')


def send_message(text, context_token):
    """发送文本消息到微信"""
    client_id = f'openclaw-weixin-{random.randint(0, 0xFFFFFFFF):08x}'
    payload = {
        'msg': {
            'from_user_id': '',
            'to_user_id': TO_USER,
            'client_id': client_id,
            'message_type': 2,
            'message_state': 2,
            'context_token': context_token,
            'item_list': [{'type': 1, 'text_item': {'text': text}}]
        },
        'base_info': BASE_INFO
    }
    r = requests.post(
        f'{BASE_URL}/ilink/bot/sendmessage',
        headers=_make_headers(),
        json=payload,
        timeout=15
    )
    return r.status_code, r.text


def listen_for_token(timeout=45):
    """长轮询 getupdates，捕获消息并提取 context_token"""
    print(f'[Listen] 开始监听 (timeout={timeout}s)...')
    r = requests.post(
        f'{BASE_URL}/ilink/bot/getupdates',
        headers=_make_headers(),
        json={'base_info': BASE_INFO},
        timeout=timeout + 5
    )
    data = r.json()
    msgs = data.get('msgs', [])
    if msgs:
        for m in msgs:
            ct = m.get('context_token', '')
            from_id = m.get('from_user_id', '')
            text_items = [
                i.get('text_item', {}).get('text', '')
                for i in m.get('item_list', [])
                if i.get('type') == 1
            ]
            text = ' '.join(text_items)
            print(f'[Listen] 收到: from={from_id} text={text}')
            save_token(ct, from_id)
            return ct, from_id, text
    print('[Listen] 超时，无新消息')
    return None, None, None


def status():
    """查看当前 token 状态"""
    token, from_id, updated = read_token()
    if token is None:
        print('状态: 无缓存 token')
        return
    age = time.time() - updated
    age_str = f'{int(age)}秒' if age < 60 else f'{int(age/60)}分钟前'
    print(f'状态: 已缓存')
    print(f'Token: {token[:30]}...')
    print(f'来源: {from_id}')
    print(f'时效: {age_str}')
    # 警告：token 超过30分钟可能失效
    if age > 1800:
        print('⚠️ Token 已超过30分钟，建议重新获取')


def cmd_send(text):
    """发送消息命令"""
    token, from_id, updated = read_token()
    if token is None:
        print('[错误] 没有缓存 token！请先在微信给 ClawBot 发一条消息，再运行 listen 捕获。')
        sys.exit(1)

    age = time.time() - updated
    if age > 1800:
        print(f'[警告] Token 已 {int(age/60)} 分钟，可能已过期，尝试刷新...')
        print(f'[提示] 请先在微信给 ClawBot 发一条新消息，然后回车继续...')
        input()
        new_token, _, _ = listen_for_token(timeout=60)
        if new_token:
            token = new_token
        else:
            print('[警告] 刷新失败，用旧 token 尝试...')

    print(f'[发送] {text[:50]}{"..." if len(text) > 50 else ""}')
    code, body = send_message(text, token)
    if code == 200:
        print(f'[成功] HTTP {code}')
    else:
        print(f'[失败] HTTP {code}: {body[:200]}')
    return code


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'send':
        if len(sys.argv) < 3:
            print('用法: python wechat_forward.py send "消息内容"')
            sys.exit(1)
        text = sys.argv[2]
        cmd_send(text)

    elif cmd == 'listen':
        timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 45
        ct, fid, text = listen_for_token(timeout)
        if ct:
            print(f'\n✅ 成功捕获 token，已保存。现在可以用 send 发送消息了。')

    elif cmd == 'status':
        status()

    else:
        print(f'未知命令: {cmd}')
        print(__doc__)


if __name__ == '__main__':
    main()
