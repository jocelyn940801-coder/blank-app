import streamlit as st
import pandas as pd
import plotly.express as px
from itertools import combinations


# -----------------------------
# 網頁基本設定
# -----------------------------
st.set_page_config(
    page_title="桌球選手贊助 ROI 分析",
    page_icon="🏓",
    layout="wide"
)

st.title("🏓 桌球選手贊助投資報酬分析")
st.write(
    "協助企業根據預算、曝光效果與選手表現，"
    "比較不同贊助方案的投資效益。"
)


# -----------------------------
# 讀取資料
# -----------------------------
df = pd.read_csv("players.csv")


# -----------------------------
# 側邊欄設定
# -----------------------------
st.sidebar.header("分析設定")

scenario = st.sidebar.selectbox(
    "選擇分析情境",
    ["保守情境", "一般情境", "樂觀情境"]
)

scenario_multiplier = {
    "保守情境": 0.8,
    "一般情境": 1.0,
    "樂觀情境": 1.2
}

multiplier = scenario_multiplier[scenario]

exposure_value = st.sidebar.slider(
    "每 1,000 次曝光的價值（元）",
    min_value=50,
    max_value=500,
    value=150,
    step=10
)

budget = st.sidebar.number_input(
    "公司總贊助預算（元）",
    min_value=0,
    value=3000000,
    step=100000
)

st.sidebar.caption(
    "保守情境：曝光人數 × 80%\n\n"
    "一般情境：曝光人數 × 100%\n\n"
    "樂觀情境：曝光人數 × 120%"
)


# -----------------------------
# 財務指標計算
# -----------------------------
df["情境曝光人數"] = (
    df["預估曝光人數"] * multiplier
).round().astype(int)

df["預估曝光價值"] = (
    df["情境曝光人數"] / 1000 * exposure_value
)

df["預估淨收益"] = (
    df["預估曝光價值"] - df["贊助成本"]
)

df["ROI (%)"] = (
    df["預估淨收益"] / df["贊助成本"] * 100
).round(2)

df["每千次曝光成本"] = (
    df["贊助成本"] / df["情境曝光人數"] * 1000
).round(2)

df["損益兩平 CPM"] = (
    df["贊助成本"] / df["情境曝光人數"] * 1000
).round(2)

def investment_decision(roi):
    if roi > 0:
        return "值得考慮"
    elif roi == 0:
        return "損益兩平"
    else:
        return "風險較高"


df["投資判斷"] = df["ROI (%)"].apply(
    investment_decision
)

# -----------------------------
# 單一選手推薦
# -----------------------------
available = df[df["贊助成本"] <= budget]

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "分析情境",
    scenario
)

col2.metric(
    "預算內可選選手",
    f"{len(available)} 位"
)

if not available.empty:
    best_player = available.loc[
        available["ROI (%)"].idxmax()
    ]

    col3.metric(
        "單一選手推薦",
        best_player["選手"]
    )

    col4.metric(
        "最高預估 ROI",
        f'{best_player["ROI (%)"]:.2f}%'
    )
else:
    col3.metric("單一選手推薦", "預算不足")
    col4.metric("最高預估 ROI", "—")


# -----------------------------
# 財務分析表格
# -----------------------------
st.subheader("選手財務分析")

st.dataframe(
    df[
        [
            "選手",
            "國家地區",
            "世界排名",
            "排名積分",
            "勝率",
            "贊助成本",
            "情境曝光人數",
            "預估曝光價值",
            "預估淨收益",
            "ROI (%)",
            "損益兩平 CPM",
            "投資判斷"
        ]
    ],
    use_container_width=True,
    hide_index=True
)


# -----------------------------
# ROI 比較圖
# -----------------------------
st.subheader("不同選手的預估 ROI")

fig_roi = px.bar(
    df.sort_values("ROI (%)", ascending=False),
    x="選手",
    y="ROI (%)",
    color="ROI (%)",
    title=f"{scenario}下的贊助 ROI",
    color_continuous_scale="RdYlGn"
)

fig_roi.add_hline(
    y=0,
    line_dash="dash",
    line_color="black",
    annotation_text="損益兩平線"
)

st.plotly_chart(
    fig_roi,
    use_container_width=True
)


# -----------------------------
# 成本與曝光價值圖
# -----------------------------
st.subheader("贊助成本與曝光價值比較")

fig_scatter = px.scatter(
    df,
    x="贊助成本",
    y="預估曝光價值",
    size="情境曝光人數",
    color="ROI (%)",
    hover_name="選手",
    hover_data=[
        "國家地區",
        "世界排名",
        "排名積分",
        "勝率"
    ],
    title="贊助成本與預估曝光價值",
    color_continuous_scale="RdYlGn"
)

st.plotly_chart(
    fig_scatter,
    use_container_width=True
)


# -----------------------------
# 最佳贊助組合分析
# -----------------------------
st.subheader("💼 預算內最佳贊助組合")

best_combo = []
best_total_profit = 0
best_total_cost = 0
best_total_value = 0

for number_of_players in range(1, len(df) + 1):
    for combo in combinations(df.index, number_of_players):
        combo_list = list(combo)

        total_cost = df.loc[
            combo_list, "贊助成本"
        ].sum()

        total_profit = df.loc[
            combo_list, "預估淨收益"
        ].sum()

        total_value = df.loc[
            combo_list, "預估曝光價值"
        ].sum()

        if (
            total_cost <= budget
            and total_profit > best_total_profit
        ):
            best_combo = combo_list
            best_total_profit = total_profit
            best_total_cost = total_cost
            best_total_value = total_value


if best_combo:
    selected_names = df.loc[
        best_combo, "選手"
    ].tolist()

    portfolio_roi = (
        best_total_profit / best_total_cost * 100
    )

    st.success(
        "推薦贊助組合："
        + "、".join(selected_names)
    )

    portfolio_col1, portfolio_col2, portfolio_col3 = (
        st.columns(3)
    )

    portfolio_col1.metric(
        "組合總成本",
        f"NT$ {best_total_cost:,.0f}"
    )

    portfolio_col2.metric(
        "組合預估淨收益",
        f"NT$ {best_total_profit:,.0f}"
    )

    portfolio_col3.metric(
        "組合預估 ROI",
        f"{portfolio_roi:.2f}%"
    )

    st.write("組合包含的選手：")

    st.dataframe(
        df.loc[
            best_combo,
            [
                "選手",
                "世界排名",
                "贊助成本",
                "預估曝光價值",
                "預估淨收益",
                "ROI (%)"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning(
        "目前預算及分析假設下，"
        "沒有預估淨收益為正的贊助組合。"
    )


# -----------------------------
# ROI 敏感度分析
# -----------------------------
st.subheader("📈 ROI 敏感度分析")

selected_player = st.selectbox(
    "選擇要進行敏感度分析的選手",
    df["選手"].tolist()
)

player_data = df[
    df["選手"] == selected_player
].iloc[0]

cpm_values = list(range(50, 501, 25))

sensitivity_rows = []

for cpm in cpm_values:
    estimated_value = (
        player_data["情境曝光人數"] / 1000 * cpm
    )

    estimated_profit = (
        estimated_value - player_data["贊助成本"]
    )

    estimated_roi = (
        estimated_profit
        / player_data["贊助成本"]
        * 100
    )

    sensitivity_rows.append(
        {
            "每千次曝光價值": cpm,
            "ROI (%)": round(estimated_roi, 2)
        }
    )

sensitivity_df = pd.DataFrame(sensitivity_rows)

fig_sensitivity = px.line(
    sensitivity_df,
    x="每千次曝光價值",
    y="ROI (%)",
    markers=True,
    title=f"{selected_player} 的 ROI 敏感度"
)

fig_sensitivity.add_hline(
    y=0,
    line_dash="dash",
    line_color="red",
    annotation_text="損益兩平"
)

st.plotly_chart(
    fig_sensitivity,
    use_container_width=True
)

st.write(
    f"{selected_player} 的損益兩平 CPM 約為 "
    f'NT$ {player_data["損益兩平 CPM"]:,.2f}。'
)


# -----------------------------
# 分析結論
# -----------------------------
st.subheader("分析結論")

if not available.empty:
    if best_player["ROI (%)"] > 0:
        st.success(
            f"在 {budget:,.0f} 元預算、"
            f"{scenario}及每千次曝光價值 "
            f"{exposure_value} 元的假設下，"
            f'單一選手建議選擇 {best_player["選手"]}，'
            f'其預估 ROI 為 '
            f'{best_player["ROI (%)"]:.2f}%。'
        )
    else:
        st.warning(
            "雖然目前預算可以贊助部分選手，"
            "但在目前假設下，所有可選方案的 "
            "ROI 皆小於或等於 0。"
        )
else:
    st.warning(
        "目前預算不足以贊助資料中的任何選手。"
    )


# -----------------------------
# 資料說明
# -----------------------------
st.info(
    "資料說明：世界排名與排名積分參考 "
    "ITTF 2026 年第 44 週排名；"
    "勝率、贊助成本與曝光人數為課堂分析用模擬資料，"
    "不代表選手的實際合約或真實商業價值。"
)