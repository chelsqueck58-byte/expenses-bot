import os
import requests
from datetime import datetime, timezone, timedelta

# Config
NOTION_TOKEN = os.environ['NOTION_TOKEN']
NOTION_DB_ID = os.environ['NOTION_DB_ID']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

HKT = timezone(timedelta(hours=8))
today = datetime.now(HKT).date()

def get_today_expenses():
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    payload = {
        "filter": {
            "property": "Date",
            "date": {"equals": str(today)}
        }
    }
    res = requests.post(url, headers=headers, json=payload)
    return res.json().get("results", [])

def parse_expenses(results):
    expenses = []
    for r in results:
        props = r["properties"]
        def get(key, type_):
            try:
                if type_ == "text":
                    return props[key]["rich_text"][0]["plain_text"]
                if type_ == "number":
                    return props[key]["number"]
                if type_ == "select":
                    return props[key]["select"]["name"]
                if type_ == "date":
                    return props[key]["date"]["start"]
            except:
                return None
        expenses.append({
            "merchant": get("Merchant", "text"),
            "amount": get("Amount", "number"),
            "currency": get("Currency (Local)", "select"),
            "amount_sgd": get("Amount (SGD)", "number"),
            "category": get("Category", "select"),
            "card": get("Card", "select"),
        })
    return expenses

def format_message(expenses):
    if not expenses:
        return f"📊 *Daily Spend — {today.strftime('%d %b')}*\n\nNo transactions today."

    # Group by category, food & drinks first
    categories = {}
    for e in expenses:
        cat = e["category"] or "Misc"
        categories.setdefault(cat, []).append(e)

    order = ["Food & Drinks", "Transport", "Shopping", "Health", "Recreation", "Misc"]
    cat_emojis = {
        "Food & Drinks": "🍜",
        "Transport": "🚇",
        "Shopping": "🛍",
        "Health": "💊",
        "Recreation": "🎉",
        "Misc": "📦"
    }

    lines = [f"📊 *Daily Spend — {today.strftime('%d %b')}*", "─────────────────"]

    total_hkd = 0
    total_sgd = 0

    sorted_cats = sorted(categories.keys(), key=lambda x: order.index(x) if x in order else 99)

    for cat in sorted_cats:
        items = categories[cat]
        cat_total = sum(e["amount"] or 0 for e in items)
        cat_currency = items[0]["currency"] or "HKD"
        emoji = cat_emojis.get(cat, "📦")
        lines.append(f"\n{emoji} *{cat}*  {cat_currency} {cat_total:,.2f}")
        for e in items:
            lines.append(f"   {e['merchant']}  {e['am
