"""
工单填写入口 — 支持命令行参数，也支持直接改 main() 里的参数
用法：
  python fill_form.py                                    # 使用 main() 里的硬编码参数
  python fill_form.py --reporter "zhenglong.jin" ...    # 使用命令行参数
"""
import asyncio
import argparse
from workorder_lib import fill_work_order

def get_args():
    parser = argparse.ArgumentParser(description="工单填写")
    parser.add_argument('--reporter', default=None, help='报修人搜索关键词（账号）')
    parser.add_argument('--match', default=None, help='报修人匹配文字')
    parser.add_argument('--category1', default=None, help='一级分类')
    parser.add_argument('--category2', default=None, help='二级分类')
    parser.add_argument('--phenomenon', default=None, help='问题现象')
    parser.add_argument('--cause', default=None, help='问题原因')
    parser.add_argument('--steps', default=None, help='处理步骤（用\\n分行）')
    parser.add_argument('--accept_date', default=None, help='接单日期 YYYY/MM/DD')
    parser.add_argument('--accept_time', default=None, help='接单时间 HH:MM')
    parser.add_argument('--close_date', default=None, help='关单日期')
    parser.add_argument('--close_time', default=None, help='关单时间')
    return parser.parse_args()

async def main():
    # ============ 硬编码参数（命令行无参数时使用） ============
    await fill_work_order(
        reporter_search="zhiqiangzq.xiong",
        reporter_match=None,
        category1="硬件支持",
        category2="更换电脑",
        phenomenon="主机系统版本为win10，需要更换主机",
        cause="主机系统版本过低，无法满足使用需求，需更换新主机",
        steps="1.为用户更换新主机\n2.迁移数据并完成系统配置",
        accept_date="2026/05/17",
        accept_time="14:00",
        close_date="2026/05/17",
        close_time="14:08",
    )

if __name__ == '__main__':
    args = get_args()
    if args.reporter:
        # 命令行有参数，用命令行的
        asyncio.run(fill_work_order(
            reporter_search=args.reporter,
            reporter_match=args.match,
            category1=args.category1,
            category2=args.category2,
            phenomenon=args.phenomenon or "",
            cause=args.cause or "",
            steps=args.steps or "",
            accept_date=args.accept_date or "",
            accept_time=args.accept_time or "",
            close_date=args.close_date or "",
            close_time=args.close_time or "",
        ))
    else:
        asyncio.run(main())
