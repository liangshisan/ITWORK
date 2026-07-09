"""
工单填写入口 — 只改这里的参数，不要改 workorder_lib.py 和 workorder_submit.py
"""
import asyncio
from workorder_lib import fill_work_order

async def main():
    # ============ 每次提工单只改这里 ============
    today = "2026/07/09"
    await fill_work_order(
        reporter_search="周新慧",
        category1="软件支持",
        category2="其它软件问题",
        phenomenon="无法登录税务系统查询客户发票是否真实",
        cause="浏览器缺少税务系统所需插件，导致无法正常访问",
        steps="1.接到用户反馈无法登录税务系统查发票\n2.确认浏览器缺少税务系统插件\n3.安装税务系统所需插件后恢复正常",
        accept_date=today,
        accept_time="11:00",
        close_date=today,
        close_time="11:05",
    )

asyncio.run(main())
