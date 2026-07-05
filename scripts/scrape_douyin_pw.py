#!/usr/bin/env python3
"""
抖店数据抓取 v2 — Playwright persistent_context。
抓首页经营概览 + 翻页订单列表 → 输出结构化 JSON。
登录态持久化在 data/playwright-data/，一次扫码后续免登。
用法: python3 scripts/scrape_douyin_pw.py [--orders] [--max-days 14]
"""

import time, json, re, sys, os, argparse
from datetime import datetime, timedelta
from collections import defaultdict
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE, 'data', 'scraped')
PW_DATA_DIR = os.path.join(BASE, 'data', 'playwright-data')
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PW_DATA_DIR, exist_ok=True)

HOMEPAGE_URL = 'https://fxg.jinritemai.com/ffa/mshop/homepage/index'
ADS_URL = 'https://fxg.jinritemai.com/ffa/mads/ad/manage'
ORDER_URL = 'https://fxg.jinritemai.com/ffa/morder/order/list'


def wait_for_login(page, timeout=180):
    print("🔐 需要登录 — 请在浏览器窗口中扫码...")
    start_ts = time.time()
    while time.time() - start_ts < timeout:
        try:
            text = page.inner_text('body')
            if '支付金额' in text or '成交订单数' in text:
                print("✅ 登录成功！")
                time.sleep(2)
                return True
            if '经营' in text and '概览' in text:
                print("✅ 已在经营概览页")
                return True
        except Exception:
            pass
        time.sleep(2)
    print("❌ 登录超时")
    return False


def _parse_num(s):
    """智能数字解析 — 支持 2.5万 → 25000, 1,770 → 1770, 81.37万 → 813700, 纯数字
    注意：% 标记由调用方处理，这里只移除不计算"""
    if not s: return None
    s = str(s).strip()
    s = s.replace('%', '').replace(',', '').strip()
    unit = 1
    if '万' in s:
        unit = 10000
        s = s.replace('万', '').strip()
    try:
        return float(s) * unit
    except ValueError:
        return s


def scrape_homepage(page):
    """抓取首页经营概览，返回结构化 dict"""
    page.goto(HOMEPAGE_URL, wait_until='domcontentloaded', timeout=60000)
    time.sleep(3)

    text = page.inner_text('body')
    if '手机登录' in text[:300] or '发送验证码' in text[:300]:
        if not wait_for_login(page):
            return None
        page.goto(HOMEPAGE_URL, wait_until='domcontentloaded', timeout=60000)
        time.sleep(3)
        text = page.inner_text('body')

    patterns = {
        'gmv':               r'用户支付金额[\s\S]*?¥\s*([\d,.]+)',
        'revenue':           r'成交金额[\s\S]*?¥\s*([\d,.]+)',
        'orders':            r'成交订单数[\s\S]*?([\d,]+)',
        'refund_amount':     r'退款金额\s*\(支付时间\)[\s\S]*?¥\s*([\d,.]+)',
        'refund_rate':       r'退款率[^\d]*([\d.]+%)',
        'impressions':       r'商品曝光(?:人数|次数)[\s\S]*?([\d.,]+\s*万?)',
        'clicks':            r'商品点击(?:人数|次数)[\s\S]*?([\d.,]+\s*万?)',
        'buyers':            r'成交人数[\s\S]*?([\d,]+)',
        'conversion_rate':   r'商品曝光[^\d]*成交转化率[^\d]*([\d.]+%)',
        'aov':               r'客单价[\s\S]*?¥\s*([\d,.]+)',
        'ad_spend':          r'投放消耗[\s\S]*?([\d.,]+)',
        'settlement_amount': r'结算金额[\s\S]*?¥\s*([\d,.]+)',
    }

    result = {
        'scrape_time': datetime.now().isoformat(),
        'source': 'douyin_homepage',
        'metrics': {},
        'day_over_day': {},
        'funnel': {},
        'ad_summary': {},
    }

    for key, pat in patterns.items():
        m = re.search(pat, text, re.DOTALL)
        if m:
            result['metrics'][key] = _parse_num(m.group(1))

    # 日环比
    dod_pats = {
        'gmv':         r'用户支付金额[\s\S]*?较昨日[\s\S]*?([\d.]+%)',
        'orders':      r'成交订单数[\s\S]*?较昨日[\s\S]*?([\d.]+%)',
        'impressions': r'商品曝光人数[\s\S]*?较昨日[\s\S]*?([\d.]+%)',
        'clicks':      r'商品点击人数[\s\S]*?较昨日[\s\S]*?([\d.]+%)',
        'buyers':      r'成交人数[\s\S]*?较昨日[\s\S]*?([\d.]+%)',
        'refund':      r'退款金额[\s\S]*?较昨日[\s\S]*?([\d.]+%)',
        'aov':         r'客单价[\s\S]*?较昨日[\s\S]*?([\d.]+%)',
    }
    for key, pat in dod_pats.items():
        m = re.search(pat, text, re.DOTALL)
        if m:
            result['day_over_day'][key + '_dod'] = m.group(1)

    result['funnel'] = {
        'impressions': result['metrics'].get('impressions', 0),
        'clicks': result['metrics'].get('clicks', 0),
        'buyers': result['metrics'].get('buyers', 0),
    }

    rank_m = re.search(r'7日店铺排行[^第]*第\s*(\d+)\s*名', text)
    if rank_m:
        result['store_rank'] = int(rank_m.group(1))

    # 尝试抓广告页摘要
    try:
        ad_page = page.context.new_page()
        ad_page.goto(ADS_URL, wait_until='domcontentloaded', timeout=30000)
        time.sleep(3)
        ad_text = ad_page.inner_text('body')
        m = re.search(r'投放消耗[\s\S]*?(\d[\d,.]*)', ad_text)
        if m: result['ad_summary']['total_spend'] = _parse_num(m.group(1))
        m = re.search(r'ROI[\s\S]*?(\d+\.?\d*)', ad_text)
        if m: result['ad_summary']['roi'] = _parse_num(m.group(1))
        ad_page.close()
    except Exception as e:
        print(f'  ⚠️ 广告页跳过: {e}')

    return result


def extract_page_orders(page):
    text = page.inner_text('body')
    pattern = r'订单编号[\xa0\s]*(\d{16,})'
    blocks = list(re.finditer(pattern, text))

    orders = []
    for i, mt in enumerate(blocks):
        order_id = mt.group(1)
        start = mt.start()
        end = blocks[i + 1].start() if i + 1 < len(blocks) else min(start + 1500, len(text))
        block = text[start:end]

        tm = re.search(r'下单时间[\xa0\s]*(\d{4}-\d{2}-\d{2}\s*\d{2}:\d{2}:\d{2})', block)
        order_time = tm.group(1).strip() if tm else ''
        order_date = order_time.split(' ')[0] if order_time else ''

        pm = re.search(r'¥\s*(\d+\.?\d*)\s*x\s*(\d+)', block)
        unit_price = float(pm.group(1)) if pm else 0.0
        quantity = int(pm.group(2)) if pm else 1

        sm = re.search(r'(待发货|待支付|已发货|已完成|已关闭|售后中)', block)
        status = sm.group(1) if sm else '未知'

        revenue = unit_price * quantity
        if sm:
            after = block[sm.end():]
            rev_m = re.search(r'¥\s*(\d+\.?\d*)', after)
            if rev_m: revenue = float(rev_m.group(1))

        orders.append({
            'order_id': order_id, 'order_time': order_time, 'date': order_date,
            'unit_price': unit_price, 'quantity': quantity,
            'gmv': round(unit_price * quantity, 2), 'revenue': revenue, 'status': status,
        })
    return orders


def click_next_page(page):
    try:
        btn = page.query_selector('text=下一页')
        if btn and btn.is_visible():
            btn.click(); time.sleep(3); return True
        js = page.evaluate("""()=>{
          var els=document.querySelectorAll('*');
          for(var i=0;i<els.length;i++){
            var t=els[i].textContent||els[i].innerText||'';
            if(t.trim()==='下一页'&&els[i].offsetParent&&!els[i].disabled){
              els[i].click();return'clicked';}}
          var a=document.querySelector('.auxo-pagination-next');
          if(a&&a.offsetParent){a.click();return'clicked-arrow';}
          return'not-found';}""")
        if 'clicked' in str(js): time.sleep(3); return True
        return False
    except Exception as e:
        print(f'    翻页异常: {e}'); return False


def scrape_orders(page, max_pages=500, max_days_back=14):
    page.goto(ORDER_URL, wait_until='domcontentloaded', timeout=60000)
    time.sleep(5)
    text = page.inner_text('body')
    if '手机登录' in text[:300]:
        if not wait_for_login(page): return []
        page.goto(ORDER_URL, wait_until='domcontentloaded', timeout=60000)
        time.sleep(4)

    all_orders = []
    cutoff = (datetime.now() - timedelta(days=max_days_back)).strftime('%Y-%m-%d')

    for pg in range(max_pages):
        print(f'  📄 第 {pg + 1} 页 ...', end=' ', flush=True)
        time.sleep(1.5)
        orders = extract_page_orders(page)
        if not orders: print('无订单，停止'); break
        all_orders.extend(orders)
        oldest = min((o['date'] for o in orders if o['date']), default='')
        print(f'{len(orders)} 条, 最早 {oldest}')
        if oldest and oldest < cutoff:
            print(f'  ✅ 已覆盖 {oldest}'); break
        if not click_next_page(page): print('  无下一页，停止'); break
    return all_orders


def compute_daily(orders):
    daily = defaultdict(lambda: {'gmv': 0, 'orders': 0, 'revenue': 0})
    for o in orders:
        if o['date']:
            daily[o['date']]['gmv'] += o['gmv']
            daily[o['date']]['orders'] += 1
            daily[o['date']]['revenue'] += o['revenue']
    return dict(sorted(daily.items()))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--orders', action='store_true')
    p.add_argument('--max-days', type=int, default=14)
    args = p.parse_args()

    print("=" * 60)
    print("📊 抖店数据抓取 (Playwright v2)")
    print("=" * 60)

    with sync_playwright() as pw:
        print("🖥  启动浏览器（持久化 Profile）...")
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=PW_DATA_DIR,
            headless=False,
            viewport={'width': 1440, 'height': 900},
            args=['--disable-blink-features=AutomationControlled'],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        orders = []

        try:
            print("\n1️⃣ 抓取首页经营概览...")
            hp = scrape_homepage(page)
            if hp is None:
                print("❌ 无法获取首页数据（登录失败）")
                return
            mt = hp.get('metrics', {})
            print(f"   GMV: ¥{mt.get('gmv', 'N/A')} | 订单: {mt.get('orders', 'N/A')} | 曝光: {mt.get('impressions', 'N/A')}")

            if args.orders:
                print("\n2️⃣ 抓取订单列表（翻页中）...")
                orders = scrape_orders(page, max_days_back=args.max_days)
                print(f"   共抓取 {len(orders)} 条订单")
                daily = compute_daily(orders)
                for day in sorted(daily.keys()):
                    d = daily[day]
                    print(f"   {day}: GMV=¥{d['gmv']:.2f} 订单={d['orders']}")

            output = {
                'scrape_time': datetime.now().isoformat(),
                'homepage': hp,
                'orders_total': len(orders),
                'daily_aggregates': compute_daily(orders) if orders else {},
                'orders': orders,
                '_meta': {'cookies_persisted': True, 'next_run_no_relogin': True},
            }

            today = datetime.now().strftime('%Y-%m-%d')
            fp = os.path.join(DATA_DIR, f'douyin_{today}.json')
            with open(fp, 'w') as f: json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"   ✅ {fp}")
            lp = os.path.join(DATA_DIR, 'latest.json')
            with open(lp, 'w') as f: json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"   ✅ {lp}")
            print("=" * 60)
            print("✅ 完成 — 登录态已持久化，下次运行无需重新登录")

        finally:
            print("\n🔒 关闭浏览器...")
            ctx.close()


if __name__ == '__main__':
    main()
