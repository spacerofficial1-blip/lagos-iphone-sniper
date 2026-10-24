import streamlit as st
import pandas as pd
from scraper_engine import (
    load_config,
    save_config,
    evaluate_listing,
    run_automated_sweep,
    DEFAULT_CONFIG
)

st.set_page_config(
    page_title="Lagos iPhone 12–14 Pro Max Sniper",
    page_icon="📱",
    layout="wide"
)

st.title("📱 Lagos iPhone 12–14 Pro Max Deal Sniper & Flip Engine")
st.caption("Automated Jiji.ng & Facebook Marketplace Arbitrage • Local Ikeja Soft OLED Calculator • Fast-Turnover Pricing")

config = load_config()

# --- SIDEBAR: GLOBAL VELOCITY & PROFIT SETTINGS ---
st.sidebar.header("⚡ Velocity & Flip Rules")

fast_discount = st.sidebar.slider(
    "Fast-Turnover Resale Discount (₦)",
    min_value=10000,
    max_value=40000,
    value=int(config.get("fast_turnover_discount_ngn", 25000)),
    step=5000,
    help="Reduces your target selling price below Computer Village clean market value so your phones sell within 24–48 hours."
)

min_profit = st.sidebar.number_input(
    "Minimum Target Net Profit Per Phone (₦)",
    min_value=20000,
    max_value=250000,
    value=int(config.get("min_profit_threshold_ngn", 45000)),
    step=5000
)

use_auto_jiji = st.sidebar.toggle(
    "Use Automatic Jiji Lagos Median Price",
    value=bool(config.get("use_auto_jiji_benchmark", False)),
    help="When OFF, uses your Manual Computer Village Clean Price table. When ON, uses the live scraped Jiji Lagos median."
)

if st.sidebar.button("💾 Save Global Settings", use_container_width=True):
    config["fast_turnover_discount_ngn"] = fast_discount
    config["min_profit_threshold_ngn"] = min_profit
    config["use_auto_jiji_benchmark"] = use_auto_jiji
    save_config(config)
    st.sidebar.success("Settings saved!")

st.sidebar.divider()
st.sidebar.markdown("### 📲 Mobile Bookmarklet (FB Workaround 3)")
st.sidebar.caption("Scrolling Facebook Marketplace on your phone? Paste any listing in Tab 2 to get the instant repair & flip math in 1 second.")

# --- MAIN TABS ---
tab1, tab2, tab3 = st.tabs([
    "🎯 Live Deal Sniper Feed",
    "⚡ Instant Deal & FB Evaluator",
    "🛠️ Computer Village & Local Soft OLED Pricing Table"
])

# === TAB 1: LIVE SNIPER FEED ===
with tab1:
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        st.subheader("Live Lagos Deal Scanner (Jiji.ng + FB Cloud)")
    with col_b:
        only_winners = st.checkbox("Show Only Profitable Deals", value=True)
    with col_c:
        scan_btn = st.button("🚀 Run Live Lagos Sweep Now", type="primary", use_container_width=True)

    if scan_btn:
        with st.spinner("Scanning newest Jiji.ng Lagos & Facebook Marketplace listings across iPhone 12 to 14 Pro Max..."):
            deals = run_automated_sweep()
            st.session_state["last_deals"] = deals

    deals_list = st.session_state.get("last_deals", [])
    if only_winners:
        deals_list = [d for d in deals_list if d["is_winning_deal"]]

    if not deals_list:
        st.info("Click **'🚀 Run Live Lagos Sweep Now'** above to pull real-time Lagos listings, or inspect/test any Jiji or Facebook deal in **Tab 2**.")
    else:
        st.success(f"Showing {len(deals_list)} matching Lagos opportunities.")
        for d in sorted(deals_list, key=lambda x: x["expected_net_profit"], reverse=True):
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    st.markdown(f"### {d['model']} — {d['deal_category']}")
                    st.write(f"**Listing Title:** {d['title']}")
                    st.caption(f"Source: {d['source']} | {d['warning_badge']}")
                    if d["description"]:
                        st.write(f"_{d['description']}_")
                with c2:
                    st.metric("Seller Asking Price", f"₦{d['asking_price']:,}")
                    st.write(f"**Local Repair Cost:** {d['repair_summary']}")
                    st.write(f"**Your All-In Cost:** `₦{d['all_in_cost']:,}`")
                    st.write(f"**Max Walk-Away Offer:** `₦{d['recommended_max_offer']:,}`")
                with c3:
                    st.metric(
                        "Expected Net Profit",
                        f"₦{d['expected_net_profit']:,}",
                        delta=f"{d['roi_percent']}% ROI"
                    )
                    st.write(f"**CV Clean Price:** ₦{d['benchmark_clean_price']:,}")
                    st.write(f"**Quick-Sale Price (-₦{d['fast_turnover_discount']:,}):** `₦{d['your_quick_sale_price']:,}`")
                    st.link_button("💬 1-Click WhatsApp Seller", d["whatsapp_url"], use_container_width=True)
                    st.link_button("🔗 Open Original Ad", d["url"], use_container_width=True)

# === TAB 2: INSTANT DEAL & FACEBOOK EVALUATOR ===
with tab2:
    st.subheader("⚡ Instant Facebook Marketplace & Jiji Deal Evaluator")
    st.write("Paste any listing title, description, and asking price from Facebook Marketplace or Jiji to calculate your exact Soft OLED repair margin, fast-turnover resale price, and 1-click WhatsApp offer.")

    col1, col2 = st.columns(2)
    with col1:
        test_title = st.text_input("Listing Title", value="Urgent sale iPhone 13 Pro Max 128GB UK used cracked screen")
        test_desc = st.text_area(
            "Seller Description",
            value="Phone is 100% clean, Face ID working perfectly, iCloud signed out. Only the screen has a crack and small black spot at the edge. Need urgent cash today in Ikeja/Yaba."
        )
    with col2:
        test_price = st.number_input("Seller Asking Price (₦)", min_value=50000, max_value=1500000, value=320000, step=10000)
        test_phone = st.text_input("Seller Phone Number (Optional for 1-Click WhatsApp)", value="08012345678")
        test_source = st.selectbox("Platform", ["Facebook Marketplace (Lagos)", "Jiji.ng (Lagos)", "WhatsApp Status / Direct"])

    if st.button("🧮 Calculate Flip Margin & Generate Offer", type="primary"):
        result = evaluate_listing(
            title=test_title,
            description=test_desc,
            asking_price=int(test_price),
            url="https://www.facebook.com/marketplace/lagos",
            source=test_source,
            seller_phone=test_phone,
            config=config
        )
        if not result:
            st.error("Could not detect an iPhone model between iPhone 12 and iPhone 14 Pro Max. Make sure the title includes the model name (e.g., 'iPhone 13 Pro').")
        else:
            st.divider()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Detected Model", result["model"])
            m2.metric("All-In Cost (Buy + Fix)", f"₦{result['all_in_cost']:,}")
            m3.metric(f"Quick-Sale Price (-₦{result['fast_turnover_discount']:,})", f"₦{result['your_quick_sale_price']:,}")
            m4.metric("Expected Net Profit", f"₦{result['expected_net_profit']:,}", f"{result['roi_percent']}% ROI")

            st.info(
                f"**Deal Classification:** {result['deal_category']}  |  "
                f"**Repair Needed:** {result['repair_summary']}  |  "
                f"**Safety Check:** {result['warning_badge']}  |  "
                f"**Max Counter-Offer to Hit ₦{min_profit:,} Profit:** `₦{result['recommended_max_offer']:,}`"
            )
            st.link_button("💬 Click to Message Seller on WhatsApp With Pre-Filled Cash Offer", result["whatsapp_url"])

# === TAB 3: EDITABLE COMPUTER VILLAGE & LOCAL SOFT OLED PRICING TABLE ===
with tab3:
    st.subheader("🛠️ Computer Village Benchmarks & Local Ikeja Soft OLED Costs (₦)")
    st.write("Edit any cell below to match current Ikeja street prices. Your changes immediately update the sniper calculator.")

    rows = []
    for model_name, data in config["models"].items():
        rows.append({
            "Model": model_name,
            "Manual CV Clean Price (₦)": data["manual_clean_price"],
            "Auto Jiji Median (₦)": data.get("auto_clean_price", data["manual_clean_price"]),
            "Local Soft OLED Screen (₦)": data["soft_oled_cost"],
            "Back Glass Cost (₦)": data["back_glass_cost"],
            "IC Swap + Tech Labor (₦)": data["ic_labor_cost"],
        })

    df = pd.DataFrame(rows)
    edited_df = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="fixed")

    col_save, col_reset = st.columns([1, 1])
    with col_save:
        if st.button("✅ Save Updated Price Table", type="primary", use_container_width=True):
            for _, row in edited_df.iterrows():
                m_key = row["Model"]
                if m_key in config["models"]:
                    config["models"][m_key]["manual_clean_price"] = int(row["Manual CV Clean Price (₦)"])
                    config["models"][m_key]["soft_oled_cost"] = int(row["Local Soft OLED Screen (₦)"])
                    config["models"][m_key]["back_glass_cost"] = int(row["Back Glass Cost (₦)"])
                    config["models"][m_key]["ic_labor_cost"] = int(row["IC Swap + Tech Labor (₦)"])
            save_config(config)
            st.success("All Computer Village benchmarks and Local Soft OLED screen prices updated!")
    with col_reset:
        if st.button("🔄 Reset to Default Lagos Prices", use_container_width=True):
            save_config(DEFAULT_CONFIG)
            st.rerun()
