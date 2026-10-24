import os
import re
import json
import time
import urllib.parse
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests
from bs4 import BeautifulSoup

CONFIG_FILE = "market_config.json"
SEEN_ADS_FILE = "seen_listings.json"

# Default Lagos Computer Village Clean Benchmarks & Ikeja Local Wholesale Soft OLED Costs (NGN)
DEFAULT_CONFIG = {
    "fast_turnover_discount_ngn": 25000,
    "min_profit_threshold_ngn": 45000,
    "scam_floor_ratio": 0.42,  # Flag if listed below 42% of clean value
    "use_auto_jiji_benchmark": False,
    "models": {
        "iPhone 12 Mini": {
            "jiji_slug": "apple-iphone-12-mini",
            "manual_clean_price": 240000,
            "auto_clean_price": 240000,
            "soft_oled_cost": 45000,
            "back_glass_cost": 12000,
            "ic_labor_cost": 15000
        },
        "iPhone 12": {
            "jiji_slug": "apple-iphone-12",
            "manual_clean_price": 310000,
            "auto_clean_price": 310000,
            "soft_oled_cost": 52000,
            "back_glass_cost": 15000,
            "ic_labor_cost": 15000
        },
        "iPhone 12 Pro": {
            "jiji_slug": "apple-iphone-12-pro",
            "manual_clean_price": 385000,
            "auto_clean_price": 385000,
            "soft_oled_cost": 58000,
            "back_glass_cost": 18000,
            "ic_labor_cost": 18000
        },
        "iPhone 12 Pro Max": {
            "jiji_slug": "apple-iphone-12-pro-max",
            "manual_clean_price": 465000,
            "auto_clean_price": 465000,
            "soft_oled_cost": 75000,
            "back_glass_cost": 20000,
            "ic_labor_cost": 20000
        },
        "iPhone 13 Mini": {
            "jiji_slug": "apple-iphone-13-mini",
            "manual_clean_price": 320000,
            "auto_clean_price": 320000,
            "soft_oled_cost": 65000,
            "back_glass_cost": 18000,
            "ic_labor_cost": 18000
        },
        "iPhone 13": {
            "jiji_slug": "apple-iphone-13",
            "manual_clean_price": 410000,
            "auto_clean_price": 410000,
            "soft_oled_cost": 75000,
            "back_glass_cost": 20000,
            "ic_labor_cost": 20000
        },
        "iPhone 13 Pro": {
            "jiji_slug": "apple-iphone-13-pro",
            "manual_clean_price": 520000,
            "auto_clean_price": 520000,
            "soft_oled_cost": 115000,
            "back_glass_cost": 22000,
            "ic_labor_cost": 25000
        },
        "iPhone 13 Pro Max": {
            "jiji_slug": "apple-iphone-13-pro-max",
            "manual_clean_price": 610000,
            "auto_clean_price": 610000,
            "soft_oled_cost": 130000,
            "back_glass_cost": 25000,
            "ic_labor_cost": 25000
        },
        "iPhone 14": {
            "jiji_slug": "apple-iphone-14",
            "manual_clean_price": 510000,
            "auto_clean_price": 510000,
            "soft_oled_cost": 110000,
            "back_glass_cost": 25000,
            "ic_labor_cost": 25000
        },
        "iPhone 14 Plus": {
            "jiji_slug": "apple-iphone-14-plus",
            "manual_clean_price": 575000,
            "auto_clean_price": 575000,
            "soft_oled_cost": 125000,
            "back_glass_cost": 28000,
            "ic_labor_cost": 25000
        },
        "iPhone 14 Pro": {
            "jiji_slug": "apple-iphone-14-pro",
            "manual_clean_price": 690000,
            "auto_clean_price": 690000,
            "soft_oled_cost": 155000,
            "back_glass_cost": 30000,
            "ic_labor_cost": 30000
        },
        "iPhone 14 Pro Max": {
            "jiji_slug": "apple-iphone-14-pro-max",
            "manual_clean_price": 790000,
            "auto_clean_price": 790000,
            "soft_oled_cost": 180000,
            "back_glass_cost": 35000,
            "ic_labor_cost": 30000
        }
    }
}

# Keyword Dictionaries for Classification
SCREEN_DEFECT_KEYWORDS = [
    "cracked screen", "crack screen", "broken screen", "screen crack",
    "bad screen", "bleeding screen", "ink on screen", "black spot", "dot on screen",
    "white screen", "green screen", "lines on screen", "line on screen",
    "touch not working", "display issue", "needs screen", "change screen", "broken glass"
]

BACK_DEFECT_KEYWORDS = [
    "cracked back", "crack back", "broken back", "back glass", "shattered back", "back pouch"
]

DISTRESS_KEYWORDS = [
    "urgent", "distress", "need cash", "need money", "emergency",
    "quick sale", "fast sale", "upgraded", "relocating", "take it today", "giveaway price"
]

FATAL_RED_FLAG_KEYWORDS = [
    "icloud lock", "locked icloud", "bypassed", "bypass", "lost mode",
    "no face id", "face id not working", "face id issue", "faceid off",
    "no service", "searching network", "baseband", "motherboard", "board issue",
    "dead phone", "not turning on", "water damage", "panic full", "restarting"
]

DEALER_SPAM_KEYWORDS = [
    "visit our office", "computer village", "otigba", "pepple street",
    "all colors available", "bulk price", "wholesale", "warranty included",
    "we deliver nationwide", "swap allowed", "bring your old phone", "installment"
]


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG


def save_config(cfg: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def load_seen_ads() -> set:
    if os.path.exists(SEEN_ADS_FILE):
        try:
            with open(SEEN_ADS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_seen_ads(seen: set) -> None:
    # Keep last 2000 IDs so file stays tiny
    trimmed = list(seen)[-2000:]
    with open(SEEN_ADS_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed, f)


def detect_exact_model(title: str, description: str = "") -> Optional[str]:
    """Strictly matches iPhone 12 series through 14 Pro Max without mixing up Base vs Pro vs Pro Max."""
    text = f"{title} {description}".lower()
    # Order from most specific (Pro Max / Plus / Mini / Pro) to base models
    ordered_patterns = [
        ("iPhone 14 Pro Max", r"\biphone\s*14\s*pro\s*max\b"),
        ("iPhone 14 Pro", r"\biphone\s*14\s*pro\b(?!\s*max)"),
        ("iPhone 14 Plus", r"\biphone\s*14\s*plus\b"),
        ("iPhone 14", r"\biphone\s*14\b(?!\s*(pro|plus|max))"),
        ("iPhone 13 Pro Max", r"\biphone\s*13\s*pro\s*max\b"),
        ("iPhone 13 Pro", r"\biphone\s*13\s*pro\b(?!\s*max)"),
        ("iPhone 13 Mini", r"\biphone\s*13\s*mini\b"),
        ("iPhone 13", r"\biphone\s*13\b(?!\s*(pro|mini|max))"),
        ("iPhone 12 Pro Max", r"\biphone\s*12\s*pro\s*max\b"),
        ("iPhone 12 Pro", r"\biphone\s*12\s*pro\b(?!\s*max)"),
        ("iPhone 12 Mini", r"\biphone\s*12\s*mini\b"),
        ("iPhone 12", r"\biphone\s*12\b(?!\s*(pro|mini|max))"),
    ]
    for model_name, pattern in ordered_patterns:
        if re.search(pattern, text):
            return model_name
    return None


def evaluate_listing(
    title: str,
    description: str,
    asking_price: int,
    url: str,
    source: str,
    seller_phone: str = "",
    posted_ago: str = "Just now",
    config: Optional[dict] = None
) -> Optional[Dict]:
    """
    Core Deal Sniper Brain:
    Calculates Clean Distress vs. Screen/Back Repair Arbitrage, applies Fast-Turnover Discount,
    and checks Dealer & Fatal Motherboard Red Flags.
    """
    if config is None:
        config = load_config()

    model_name = detect_exact_model(title, description)
    if not model_name or model_name not in config["models"]:
        return None

    m_cfg = config["models"][model_name]
    full_text = f"{title} {description}".lower()

    # 1. Check Dealer Spam vs Direct Owner
    is_dealer = any(kw in full_text for kw in DEALER_SPAM_KEYWORDS)

    # 2. Check Fatal Red Flags (Motherboard / No Face ID / iCloud)
    fatal_flags = [kw for kw in FATAL_RED_FLAG_KEYWORDS if kw in full_text]

    # 3. Detect Screen & Back Glass Defects
    has_screen_defect = any(kw in full_text for kw in SCREEN_DEFECT_KEYWORDS)
    has_back_defect = any(kw in full_text for kw in BACK_DEFECT_KEYWORDS)
    is_distress_text = any(kw in full_text for kw in DISTRESS_KEYWORDS)

    # 4. Determine Benchmark Market Price (Manual vs Auto Jiji Median)
    use_auto = config.get("use_auto_jiji_benchmark", False)
    benchmark_clean_price = (
        m_cfg.get("auto_clean_price", m_cfg["manual_clean_price"])
        if use_auto else m_cfg["manual_clean_price"]
    )

    # 5. Calculate Repair Costs
    repair_cost = 0
    repair_breakdown = []
    if has_screen_defect:
        repair_cost += m_cfg["soft_oled_cost"] + m_cfg["ic_labor_cost"]
        repair_breakdown.append(
            f"Soft OLED (₦{m_cfg['soft_oled_cost']:,}) + IC Swap Labor (₦{m_cfg['ic_labor_cost']:,})"
        )
    if has_back_defect:
        repair_cost += m_cfg["back_glass_cost"]
        # If no screen defect was triggered, add small labor fee for back glass
        if not has_screen_defect:
            repair_cost += 10000
            repair_breakdown.append(f"Back Glass + Labor (₦{m_cfg['back_glass_cost'] + 10000:,})")
        else:
            repair_breakdown.append(f"Back Glass (₦{m_cfg['back_glass_cost']:,})")

    # 6. Apply Your Fast-Turnover Discount (₦10k - ₦40k below market for instant resale)
    fast_discount = config.get("fast_turnover_discount_ngn", 25000)
    your_quick_sale_price = benchmark_clean_price - fast_discount

    # 7. Calculate Total All-In Cost & Expected Net Profit
    all_in_cost = asking_price + repair_cost
    expected_net_profit = your_quick_sale_price - all_in_cost
    roi_percent = round((expected_net_profit / max(all_in_cost, 1)) * 100, 1)

    # 8. Classify Deal Type & Status
    if has_screen_defect and has_back_defect:
        deal_category = "🔧 Screen + Back Glass Flip"
    elif has_screen_defect:
        deal_category = "📱 Cracked/Defective Screen Flip"
    elif has_back_defect:
        deal_category = "🔨 Cracked Back Glass Flip"
    elif is_distress_text or asking_price <= (benchmark_clean_price * 0.80):
        deal_category = "🔥 Clean Distress / Underpriced Flip"
    else:
        deal_category = "📊 Standard Listing"

    # Scam Floor Check
    scam_floor = benchmark_clean_price * config.get("scam_floor_ratio", 0.42)
    if not has_screen_defect and asking_price < scam_floor:
        warning_badge = "⚠️ SCAM RISK: Price Suspiciously Low (<42% Market) - Inspect In Person Only!"
    elif fatal_flags:
        warning_badge = f"⛔ RED FLAG DEFECT ({', '.join(fatal_flags[:2]).upper()})"
    elif is_dealer:
        warning_badge = "🏪 Likely CV Dealer Post"
    else:
        warning_badge = "✅ Direct Owner / High-Confidence Candidate"

    # Calculate Recommended Max Offer to Still Hit Minimum Profit
    min_profit = config.get("min_profit_threshold_ngn", 45000)
    recommended_max_offer = your_quick_sale_price - repair_cost - min_profit

    # Build 1-Click WhatsApp First-Strike Link
    clean_phone = re.sub(r"[^\d]", "", seller_phone or "")
    if clean_phone.startswith("0") and len(clean_phone) == 11:
        clean_phone = "234" + clean_phone[1:]
    whatsapp_msg = (
        f"Hello! I just saw your {model_name} listing ({title}) for ₦{asking_price:,}. "
        f"I am in Lagos with instant cash ready to inspect and buy right now if iCloud and Face ID are clean. "
        f"Where can we meet today?"
    )
    encoded_msg = urllib.parse.quote(whatsapp_msg)
    whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_msg}" if clean_phone else url

    is_winning_deal = (
        expected_net_profit >= min_profit
        and not fatal_flags
        and not is_dealer
    )

    return {
        "model": model_name,
        "title": title,
        "description": description[:280],
        "source": source,
        "posted_ago": posted_ago,
        "asking_price": asking_price,
        "repair_cost": repair_cost,
        "repair_summary": " + ".join(repair_breakdown) if repair_breakdown else "₦0 (Clean Unit)",
        "all_in_cost": all_in_cost,
        "benchmark_clean_price": benchmark_clean_price,
        "fast_turnover_discount": fast_discount,
        "your_quick_sale_price": your_quick_sale_price,
        "expected_net_profit": expected_net_profit,
        "roi_percent": roi_percent,
        "recommended_max_offer": max(recommended_max_offer, 0),
        "deal_category": deal_category,
        "warning_badge": warning_badge,
        "is_winning_deal": is_winning_deal,
        "url": url,
        "whatsapp_url": whatsapp_url,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    }


def scrape_jiji_lagos(config: dict, max_models: int = 12) -> Tuple[List[Dict], dict]:
    """
    Scrapes live Lagos listings from Jiji.ng sorted by Newest First,
    updates automatic clean benchmarks, and evaluates every listing.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-NG,en;q=0.9",
    }
    evaluated_deals = []

    for model_name, m_data in list(config["models"].items())[:max_models]:
        slug = m_data["jiji_slug"]
        # Jiji Lagos endpoint sorted by newest listings
        jiji_url = f"https://jiji.ng/lagos/mobile-phones/{slug}?sort=new"
        try:
            resp = requests.get(jiji_url, headers=headers, timeout=12)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("div.b-list-advert__gallery__item, div.b-list-advert-base")
            clean_prices_for_median = []

            for card in cards[:18]:
                title_el = card.select_one("div.b-advert-title-inner, div.qa-advert-title")
                price_el = card.select_one("div.qa-advert-price")
                desc_el = card.select_one("div.b-list-advert-base__description-text")
                link_el = card.select_one("a[href]")

                if not title_el or not price_el:
                    continue

                raw_title = title_el.get_text(strip=True)
                raw_desc = desc_el.get_text(strip=True) if desc_el else ""
                raw_price = re.sub(r"[^\d]", "", price_el.get_text(strip=True))
                if not raw_price:
                    continue

                price_val = int(raw_price)
                ad_href = link_el["href"] if link_el else ""
                full_url = f"https://jiji.ng{ad_href}" if ad_href.startswith("/") else ad_href

                # Collect clean prices to update automatic Jiji benchmark
                combined_lower = f"{raw_title} {raw_desc}".lower()
                if not any(k in combined_lower for k in SCREEN_DEFECT_KEYWORDS + FATAL_RED_FLAG_KEYWORDS):
                    if 150000 <= price_val <= 1200000:
                        clean_prices_for_median.append(price_val)

                deal = evaluate_listing(
                    title=raw_title,
                    description=raw_desc,
                    asking_price=price_val,
                    url=full_url,
                    source="Jiji.ng (Lagos)",
                    posted_ago="Newest Feed",
                    config=config
                )
                if deal:
                    evaluated_deals.append(deal)

            # Update Auto Market Median if enough clean samples found
            if len(clean_prices_for_median) >= 4:
                median_val = int(statistics.median(clean_prices_for_median))
                config["models"][model_name]["auto_clean_price"] = round(median_val, -3)

            time.sleep(0.8)  # Polite rate limit
        except Exception as e:
            print(f"[Jiji Scraper Warning] {model_name}: {e}")

    save_config(config)
    return evaluated_deals, config


def scrape_facebook_marketplace_lagos(config: dict) -> List[Dict]:
    """
    Facebook Marketplace Lagos Cloud Workaround Engine:
    - Method 1: Uses Apify Facebook Marketplace Actor if APIFY_API_TOKEN is set in environment/secrets.
    - Method 2: Uses Cookie Session GraphQL fallback if FB_COOKIE_STRING is provided.
    """
    apify_token = os.getenv("APIFY_API_TOKEN", "").strip()
    evaluated_deals = []

    if apify_token:
        # Workaround 1: Apify Free-Tier Cloud Residential Proxy Actor for Lagos Marketplace
        api_url = f"https://api.apify.com/v2/acts/apify~facebook-marketplace-scraper/run-sync-get-dataset-items?token={apify_token}"
        payload = {
            "startUrls": [
                {"url": "https://www.facebook.com/marketplace/lagos/search?query=iPhone%2012%2013%2014%20cracked%20urgent&sortBy=creation_time_descend"}
            ],
            "maxItems": 25
        }
        try:
            resp = requests.post(api_url, json=payload, timeout=45)
            if resp.status_code in (200, 201):
                items = resp.json()
                for item in items:
                    title = item.get("marketplace_listing_title") or item.get("title", "")
                    desc = item.get("redacted_description", {}).get("text", "") or item.get("description", "")
                    price_str = str(item.get("listing_price", {}).get("amount", "0"))
                    price_val = int(float(re.sub(r"[^\d.]", "", price_str) or 0))
                    item_url = item.get("listingUrl") or f"https://www.facebook.com/marketplace/item/{item.get('id', '')}"

                    if price_val > 50000:
                        deal = evaluate_listing(
                            title=title,
                            description=desc,
                            asking_price=price_val,
                            url=item_url,
                            source="FB Marketplace (Lagos)",
                            posted_ago="Just Posted",
                            config=config
                        )
                        if deal:
                            evaluated_deals.append(deal)
        except Exception as e:
            print(f"[FB Apify Workaround Warning]: {e}")

    return evaluated_deals


def send_telegram_alert(deal: Dict) -> bool:
    """Sends an instant mobile notification to your Telegram Bot with a 1-Click WhatsApp/Listing link."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not bot_token or not chat_id:
        return False

    msg = (
        f"🚨 *LAGOS IPHONE SNIPER ALERT* 🚨\n\n"
        f"📱 *Model:* {deal['model']}\n"
        f"🏷️ *Type:* {deal['deal_category']}\n"
        f"📝 *Listing:* {deal['title']}\n"
        f"📍 *Source:* {deal['source']} ({deal['posted_ago']})\n\n"
        f"💰 *Seller Asking Price:* ₦{deal['asking_price']:,}\n"
        f"🔧 *Local Soft OLED + Repair:* {deal['repair_summary']}\n"
        f"🧾 *Your All-In Cost:* ₦{deal['all_in_cost']:,}\n\n"
        f"📈 *CV Clean Market Value:* ₦{deal['benchmark_clean_price']:,}\n"
        f"⚡ *Fast-Turnover Discount:* -₦{deal['fast_turnover_discount']:,}\n"
        f"🎯 *Your Quick-Sale Price:* ₦{deal['your_quick_sale_price']:,}\n"
        f"💵 *EXPECTED NET PROFIT:* *₦{deal['expected_net_profit']:,}* ({deal['roi_percent']}% ROI)\n\n"
        f"🤝 *Max Safe Walk-Away Offer:* ₦{deal['recommended_max_offer']:,}\n"
        f"🛡️ *Status:* {deal['warning_badge']}\n\n"
        f"👉 [Open Listing Directly]({deal['url']})\n"
        f"💬 [1-Click WhatsApp Seller]({deal['whatsapp_url']})"
    )

    tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        r = requests.post(
            tg_url,
            json={
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            },
            timeout=10
        )
        return r.status_code == 200
    except Exception:
        return False


def run_automated_sweep() -> List[Dict]:
    """Executed by GitHub Actions every 10 minutes or when clicking 'Scan Now' on the Web App."""
    config = load_config()
    seen_ads = load_seen_ads()

    jiji_deals, updated_cfg = scrape_jiji_lagos(config)
    fb_deals = scrape_facebook_marketplace_lagos(updated_cfg)
    all_deals = jiji_deals + fb_deals

    new_winning_deals = []
    for deal in all_deals:
        unique_key = f"{deal['url']}_{deal['asking_price']}"
        if deal["is_winning_deal"] and unique_key not in seen_ads:
            send_telegram_alert(deal)
            seen_ads.add(unique_key)
            new_winning_deals.append(deal)

    save_seen_ads(seen_ads)
    return all_deals


if __name__ == "__main__":
    results = run_automated_sweep()
    winning = [d for d in results if d["is_winning_deal"]]
    print(f"Sweep complete. Scanned {len(results)} listings, found {len(winning)} high-margin deals.")
