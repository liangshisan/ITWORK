"""
工单填写入口 — 通过命令行参数传入，禁止硬编码
用法示例:
  python fill_form.py \
    --reporter "杨静" \
    --category1 "软件支持" \
    --category2 "其它软件问题" \
    --phenomenon "飞书打开报错" \
    --cause "连接网线时开启了VPN，导致网络冲突" \
    --steps "1.排查飞书报错原因
2.发现VPN与网线网络冲突
3.退出VPN后飞书恢复正常" \
    --accept_date "2026/7/10" --accept_time "10:30" \
    --close_date "2026/7/10" --close_time "10:35"
"""
import asyncio, argparse
from datetime import datetime
from workorder_lib import fill_work_order


def main():
    today_default = datetime.now().strftime("%Y/%m/%d")

    p = argparse.ArgumentParser(description="飞书工单填写")
    p.add_argument("--reporter", required=True, help="报修人搜索词（中文名或飞书账号）")
    p.add_argument("--category1", required=True, help="一级分类")
    p.add_argument("--category2", required=True, help="二级分类")
    p.add_argument("--phenomenon", required=True, help="问题现象")
    p.add_argument("--cause", required=True, help="问题原因")
    p.add_argument("--steps", required=True, help="处理步骤（支持 \\n 或真实换行）")
    p.add_argument("--accept_date", default=today_default, help="接单日期 YYYY/M/D")
    p.add_argument("--accept_time", default="09:00", help="接单时间 HH:MM")
    p.add_argument("--close_date", default=today_default, help="关单日期 YYYY/M/D")
    p.add_argument("--close_time", default="09:30", help="关单时间 HH:MM")
    args = p.parse_args()

    # 把 accept_date/close_date 从 "2026/7/10" 转成 "2026/07/10" 格式
    def fmt_date(d):
        parts = d.replace("-", "/").split("/")
        return f"{parts[0]}/{int(parts[1]):02d}/{int(parts[2]):02d}"

    async def run():
        await fill_work_order(
            reporter_search=args.reporter,
            category1=args.category1,
            category2=args.category2,
            phenomenon=args.phenomenon,
            cause=args.cause,
            steps=args.steps,
            accept_date=fmt_date(args.accept_date),
            accept_time=args.accept_time,
            close_date=fmt_date(args.close_date),
            close_time=args.close_time,
        )

    asyncio.run(run())


if __name__ == "__main__":
    main()
