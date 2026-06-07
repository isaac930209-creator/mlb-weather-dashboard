import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta
import pytz

# 1. 網頁基本設定
st.set_page_config(page_title="MLB 球場天氣監測與停賽系統", layout="wide")

# ==================== 🎨 視覺美學：暖色系、完美留白、消滅卡頭 ====================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Noto+Sans+TC:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stWidgetLabel"] {
        font-family: 'Inter', 'Noto Sans TC', sans-serif !important;
    }
    
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
    }
    
    [data-testid="stHorizontalBlock"] {
        gap: 1.5rem !important;
    }
    
    /* 暖色系視覺階層設計 */
    .main-title {
        font-size: 2.3rem !important;
        font-weight: 700 !important;
        color: #431407; /* 深焦糖暖棕色 */
        margin-bottom: 0.3rem !important;
    }
    .sub-title {
        font-size: 1rem !important;
        color: #EA580C; /* 暖心活力橙 */
        font-weight: 400;
        margin-bottom: 1.5rem !important;
    }
    .section-title {
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        color: #7C2D12; /* 溫暖肉桂紅棕 */
        margin-top: 0.8rem !important;
        margin-bottom: 0.8rem !important;
    }
    .chart-title {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #9A3412; /* 琥珀橘棕 */
        margin-bottom: 0.4rem !important;
    }
    .logic-note {
        font-size: 0.82rem !important;
        color: #78350F; /* 焦糖色小字 */
        margin-top: 0.5rem !important;
        opacity: 0.85;
    }
    
    /* 強制今日區塊左右兩個 Container 等高 */
    [data-testid="stVScrollTable"] {
        max-height: 230px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">MLB 球場天氣監測與停賽系統</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">即時氣象資料 ＆ 歷年停賽交叉分析</div>', unsafe_allow_html=True)

# ==================== 🛠️ 2. 大數據庫：MLB 30 支球隊資料 ====================
@st.cache_data(show_spinner=False)
def get_mlb_stadiums_database():
    return {
        "New York Yankees": {"stadium_en": "Yankee Stadium", "abbr": "NYY", "lat": 40.8296, "lon": -73.9262, "dome": False},
        "Boston Red Sox": {"stadium_en": "Fenway Park", "abbr": "BOS", "lat": 42.3467, "lon": -71.0972, "dome": False},
        "Tampa Bay Rays": {"stadium_en": "Tropicana Field", "abbr": "TB", "lat": 27.7682, "lon": -82.6534, "dome": True},
        "Baltimore Orioles": {"stadium_en": "Oriole Park", "abbr": "BAL", "lat": 39.2840, "lon": -76.6216, "dome": False},
        "Toronto Blue Jays": {"stadium_en": "Rogers Centre", "abbr": "TOR", "lat": 43.6414, "lon": -79.3894, "dome": True},
        "Chicago White Sox": {"stadium_en": "Guaranteed Rate Field", "abbr": "CWS", "lat": 41.8299, "lon": -87.6337, "dome": False},
        "Cleveland Guardians": {"stadium_en": "Progressive Field", "abbr": "CLE", "lat": 41.4962, "lon": -81.6852, "dome": False},
        "Detroit Tigers": {"stadium_en": "Comerica Park", "abbr": "DET", "lat": 42.3390, "lon": -83.0485, "dome": False},
        "Kansas City Royals": {"stadium_en": "Kauffman Stadium", "abbr": "KC", "lat": 39.0517, "lon": -94.4803, "dome": False},
        "Minnesota Twins": {"stadium_en": "Target Field", "abbr": "MIN", "lat": 44.9817, "lon": -93.2778, "dome": False},
        "Houston Astros": {"stadium_en": "Minute Maid Park", "abbr": "HOU", "lat": 29.7573, "lon": -95.3555, "dome": True},
        "Los Angeles Angels": {"stadium_en": "Angel Stadium", "abbr": "LAA", "lat": 33.8003, "lon": -117.8827, "dome": False},
        "Oakland Athletics": {"stadium_en": "Oakland Coliseum", "abbr": "OAK", "lat": 37.7516, "lon": -122.2005, "dome": False},
        "Seattle Mariners": {"stadium_en": "T-Mobile Park", "abbr": "SEA", "lat": 47.5914, "lon": -122.3325, "dome": True},
        "Texas Rangers": {"stadium_en": "Globe Life Field", "abbr": "TEX", "lat": 32.7473, "lon": -97.0819, "dome": True},
        "Atlanta Braves": {"stadium_en": "Truist Park", "abbr": "ATL", "lat": 33.8907, "lon": -84.4678, "dome": False},
        "Miami Marlins": {"stadium_en": "loanDepot park", "abbr": "MIA", "lat": 25.7783, "lon": -80.2197, "dome": True},
        "New York Mets": {"stadium_en": "Citi Field", "abbr": "NYM", "lat": 40.7571, "lon": -73.8458, "dome": False},
        "Philadelphia Phillies": {"stadium_en": "Citizens Bank Park", "abbr": "PHI", "lat": 39.9061, "lon": -75.1665, "dome": False},
        "Washington Nationals": {"stadium_en": "Nationals Park", "abbr": "WSH", "lat": 38.8730, "lon": -77.0074, "dome": False},
        "Chicago Cubs": {"stadium_en": "Wrigley Field", "abbr": "CHC", "lat": 41.9484, "lon": -87.6553, "dome": False},
        "Cincinnati Reds": {"stadium_en": "Great American Ball Park", "abbr": "CIN", "lat": 39.0979, "lon": -84.5071, "dome": False},
        "Milwaukee Brewers": {"stadium_en": "American Family Field", "abbr": "MIL", "lat": 43.0280, "lon": -87.9712, "dome": True},
        "Pittsburgh Pirates": {"stadium_en": "PNC Park", "abbr": "PIT", "lat": 40.4469, "lon": -80.0057, "dome": False},
        "St. Louis Cardinals": {"stadium_en": "Busch Stadium", "abbr": "STL", "lat": 38.6226, "lon": -90.1928, "dome": False},
        "Arizona Diamondbacks": {"stadium_en": "Chase Field", "abbr": "AZ", "lat": 33.4453, "lon": -112.0667, "dome": True},
        "Colorado Rockies": {"stadium_en": "Coors Field", "abbr": "COL", "lat": 39.7559, "lon": -104.9942, "dome": False},
        "Los Angeles Dodgers": {"stadium_en": "Dodger Stadium", "abbr": "LAD", "lat": 34.0739, "lon": -118.2400, "dome": False},
        "San Diego Padres": {"stadium_en": "Petco Park", "abbr": "SD", "lat": 32.7073, "lon": -117.1566, "dome": False},
        "San Francisco Giants": {"stadium_en": "Oracle Park", "abbr": "SF", "lat": 37.7786, "lon": -122.3893, "dome": False}
    }

STADIUM_DB = get_mlb_stadiums_database()

# ==================== 🛠️ 3. Data Pipeline A：今日即時監測 (消滅 Running 提示) ====================
@st.cache_data(show_spinner=False) # 🎯 需求 1：關閉 Streamlit 預設灰色工程字提示
def fetch_live_mlb_pipeline():
    tw_tz = pytz.timezone("Asia/Taipei")
    now_tw = datetime.now(tw_tz)
    
    if now_tw.hour >= 14:
        target_dt = now_tw + timedelta(days=1)
    else:
        target_dt = now_tw
        
    target_date_str = target_dt.strftime('%Y-%m-%d')
    mlb_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={target_date_str}"
    headers = {'User-Agent': 'MLBLivePipeline/11.0'}
    try:
        res = requests.get(mlb_url, headers=headers)
        if res.status_code != 200: return pd.DataFrame()
        games = res.json().get("dates", [{}])[0].get("games", [])
        results = []
        for g in games:
            home = g["teams"]["home"]["team"]["name"]
            away = g["teams"]["away"]["team"]["name"]
            status_raw = g["status"]["detailedState"]
            game_date_utc = g.get("gameDate")
            
            tw_time_str = "時間未定"
            if game_date_utc:
                try:
                    utc_dt = datetime.strptime(game_date_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                    tw_dt = utc_dt.astimezone(tw_tz)
                    tw_time_str = tw_dt.strftime("%H:%M")
                except: pass

            if status_raw in ["Final", "Game Over", "Completed Early"]:
                display_status = "已完賽"
            elif status_raw in ["In Progress", "Warm Up", "Manager Challenge", "Delayed Start"]:
                display_status = "進行中"
            elif status_raw == "Postponed":
                display_status = "官方宣布停賽"
            else:
                display_status = "未開打"

            weather_desc, temp_c, risk = "無氣象資料", "N/A", "🟢 安全 (開打機率高)"
            
            if home in STADIUM_DB:
                info = STADIUM_DB[home]
                if info["dome"]:
                    weather_desc, temp_c, risk = "室內巨蛋球場", "22", "🔵 巨蛋 (不受天氣影響)"
                else:
                    p_res = requests.get(f"https://api.weather.gov/points/{info['lat']},{info['lon']}", headers=headers)
                    if p_res.status_code == 200:
                        f_res = requests.get(p_res.json()["properties"]["forecastHourly"], headers=headers)
                        if f_res.status_code == 200:
                            current = f_res.json()["properties"]["periods"][0]
                            temp_f = current["temperature"]
                            temp_c = round((temp_f - 32) * 5 / 9, 1)
                            weather_desc = current["shortForecast"]
                            desc_l = weather_desc.lower()
                            if "rain" in desc_l or "thunderstorm" in desc_l: risk = "🔴 危險 (高度停賽風險)"
                            elif "shower" in desc_l or "cloudy" in desc_l: risk = "🟡 注意 (中度延遲風險)"
            
            # 若官方已宣布，強制改為停賽狀態
            if display_status == "官方宣布停賽": risk = "❌ 已停賽 (官方已宣布)"
            # 若賽事進行中，強制改為藍點識別
            elif display_status == "進行中": risk = "🔵 進行中 (賽事開打中)"
            # 若賽事已完賽，強制改為深褐點識別
            elif display_status == "已完賽": risk = "🟤 已完賽 (賽事已結束)"
            
            results.append({
                "開賽時間 (台灣時間)": tw_time_str,
                "對戰組合": f"{away} @ {home}",
                "賽事進度": display_status,
                "系統風險預測": risk,
                "球場名稱": STADIUM_DB.get(home, {"stadium_en": "Unknown Stadium"})["stadium_en"],
                "緯度": STADIUM_DB.get(home, {"lat": 37.0})["lat"], "經度": STADIUM_DB.get(home, {"lon": -95.0})["lon"],
                "即時氣象": weather_desc, "氣溫(°C)": temp_c
            })
        return pd.DataFrame(results)
    except: return pd.DataFrame()

# ==================== 🛠️ 4. Data Pipeline B：歷史大數據管線 ====================
@st.cache_data(show_spinner=False)
def fetch_all_history_pipeline():
    historical_events = []
    headers = {'User-Agent': 'MLBHistoryPipeline/11.0'}
    tw_tz = pytz.timezone("Asia/Taipei")
    now_tw = datetime.now(tw_tz)
    
    start_year = 2005
    end_year = now_tw.year
    
    for year in range(start_year, end_year + 1):
        start_date = f"{year}-04-01"
        if year == end_year:
            yesterday_dt = now_tw - timedelta(days=1)
            end_date = yesterday_dt.strftime('%Y-%m-%d')
            if yesterday_dt.month < 4: continue
        else:
            end_date = f"{year}-10-31"
            
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start_date}&endDate={end_date}"
        try:
            res = requests.get(url, headers=headers)
            if res.status_code != 200: continue
            dates_data = res.json().get("dates", [])
            for date_obj in dates_data:
                game_date = date_obj.get("date")
                month_text = f"{int(game_date.split('-')[1])}月"
                
                for game in date_obj.get("games", []):
                    if game["status"]["detailedState"] == "Postponed":
                        home_team = game["teams"]["home"]["team"]["name"]
                        away_team = game["teams"]["away"]["team"]["name"]
                        reason = game["status"].get("reason", "因雨/惡劣天氣")
                        
                        if home_team in STADIUM_DB:
                            info = STADIUM_DB[home_team]
                            historical_events.append({
                                "年份": year, "月份": month_text, "日期": game_date,
                                "主場球隊": home_team, "對戰組合": f"{away_team} @ {home_team}",
                                "球場名稱": info["stadium_en"], "球隊簡寫": info["abbr"], "異常原因": reason,
                                "緯度": info["lat"], "經度": info["lon"]
                            })
        except: continue
    return pd.DataFrame(historical_events)


# ==================== 🖥️ 5. 前端呈現 (圖例合一 ＆ 綠色校正 ＆ 準則小字) ====================

# ----------------- 【區塊一：今日即時監測與預測】 -----------------
st.markdown('<div class="section-title">今日全美球場天氣監測與停賽預報</div>', unsafe_allow_html=True)

with st.spinner("正在同步即時天氣監測數據..."):
    df_live = fetch_live_mlb_pipeline()

if df_live.empty:
    st.info("今日目前大聯盟官方無排定賽事。")
else:
    col_live1, col_live2 = st.columns([1, 1])
    
    with col_live1:
        with st.container(border=True): 
            # 🎯 需求 2：色彩群組全面整合至單一欄位，並將安全調回「健康翠綠色」
            fig_live = px.scatter_geo(
                df_live, lat="緯度", lon="經度", hover_name="球場名稱",
                hover_data=["對戰組合", "即時氣象"], color="系統風險預測",
                color_discrete_map={
                    "🟢 安全 (開打機率高)": "#10B981",      # 🎯 修正：回歸綠色指示
                    "🔵 巨蛋 (不受天氣影響)": "#3B82F6",     # 舒適亮藍
                    "🔵 進行中 (賽事開打中)": "#1D4ED8",     # 進行中深藍
                    "🟡 注意 (中度延遲風險)": "#F0D90D",      # 活力暖橘
                    "🔴 危險 (高度停賽風險)": "#EF4444",      # 警示鮮紅
                    "🟤 已完賽 (賽事已結束)": "#78350F",      # 已結束深棕
                    "❌ 已停賽 (官方已宣布)": "#431407"       # 停賽焦糖褐
                },
                projection="albers usa"
            )
            fig_live.update_layout(
                geo=dict(scope="usa", showland=True, landcolor="#FFF7ED"),
                margin={"r":10,"t":10,"l":10,"b":10},
                height=310,
                showlegend=True, # 🎯 僅保留這唯一的系統預測圖例
                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, title=None)
            )
            st.plotly_chart(fig_live, width="stretch")
        
    with col_live2:
        with st.container(border=True):
            col_title, col_btn = st.columns([2.5, 1])
            with col_title:
                st.markdown('<div class="chart-title">今日即時賽事狀態與天氣指標清單</div>', unsafe_allow_html=True)
            with col_btn:
                if st.button("強制重整天氣", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
                    
            st.dataframe(df_live[["開賽時間 (台灣時間)", "對戰組合", "賽事進度", "系統風險預測", "即時氣象"]], width="stretch", hide_index=True, height=245)

    # 🎯 需求 3：新增專業判定邏輯備註小字，提升學術報告的嚴謹度
    st.markdown('<div class="logic-note">* 系統風險判定標準：串接全美氣象局（NWS）逐時預報，當預報包含 Rain/Thunderstorm 觸發紅燈風險；包含 Shower/Cloudy 觸發黃燈注意；室內巨蛋球場與常規晴朗天氣則自動歸類為安全綠/藍燈。</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------- 【區塊二：歷史大數據分析】 -----------------
st.markdown('<div class="section-title">歷史停賽數據分析</div>', unsafe_allow_html=True)

with st.spinner("正在下載歷史數據..."):
    df_hist = fetch_all_history_pipeline()

if df_hist.empty:
    st.warning("歷史資料庫下載失敗。")
else:
    with st.container(border=True):
        col_f1, col_f2, col_f3 = st.columns([1, 1.5, 1.5])
        with col_f1:
            time_range = st.radio("歷史時間維度：", ["歷年數據", "近 5 年數據", "近 3 年數據", "近 1 年數據 (接軌至最新昨天)"], horizontal=False)
        with col_f2:
            all_teams_options = sorted(list(df_hist["主場球隊"].unique()))
            select_teams = st.multiselect("主場球隊 (可多選)：", all_teams_options)
        with col_f3:
            month_order = ["4月", "5月", "6月", "7月", "8月", "9月", "10月"]
            select_months = st.multiselect("賽季月份 (可多選)：", month_order)

    # 執行時間維度過濾
    current_year = datetime.now().year
    df_time_scoped = df_hist.copy()
    if time_range == "近 5 年數據":
        df_time_scoped = df_time_scoped[df_time_scoped["年份"] >= (current_year - 5)]
    elif time_range == "近 3 年數據":
        df_time_scoped = df_time_scoped[df_time_scoped["年份"] >= (current_year - 3)]
    elif time_range == "近 1 年數據 (接軌至最新昨天)":
        df_time_scoped = df_time_scoped[df_time_scoped["年份"] >= (current_year - 1)]

    # 圖表分流邏輯
    df_chart_scope = df_time_scoped.copy()
    if select_months:
        df_chart_scope = df_chart_scope[df_chart_scope["月份"].isin(select_months)]
        
    # 表格與 KPI 計算
    df_table_scope = df_time_scoped.copy()
    if select_teams:
        df_table_scope = df_table_scope[df_table_scope["主場球隊"].isin(select_teams)]
    if select_months:
        df_table_scope = df_table_scope[df_table_scope["月份"].isin(select_months)]

    if len(select_teams) == len(all_teams_options) or not select_teams:
        selected_teams_str = "全選球隊"
    else:
        selected_teams_str = ", ".join(select_teams)
        
    selected_months_str = ", ".join(select_months) if select_months else "全部月份"
    
    with st.container(border=True):
        st.metric(
            label=f"統計結果：【 {selected_teams_str} 】在所選範圍內的 累計總停賽場次", 
            value=f"{len(df_table_scope)} 場"
        )

    # 歷史雙圖表呈現 (1:1 對齊)
    col_hist1, col_hist2 = st.columns([1, 1])
    
    with col_hist1:
        with st.container(border=True):
            st.markdown(f'<div class="chart-title">全美停賽地理分布 ({selected_months_str})</div>', unsafe_allow_html=True)
            df_geo_count = df_chart_scope.groupby(["球場名稱", "緯度", "經度"]).size().reset_index(name="停賽次數")
            
            fig_hist_map = px.scatter_geo(
                df_geo_count, lat="緯度", lon="經度", hover_name="球場名稱",
                size="停賽次數", color="停賽次數",
                color_continuous_scale="Oranges", projection="albers usa"
            )
            fig_hist_map.update_layout(
                geo=dict(scope="usa", showland=True, landcolor="#FFF7ED"),
                margin={"r":10,"t":10,"l":10,"b":10},
                height=320,
                coloraxis_colorbar=dict(len=1.0, y=0.5, thickness=15)
            )
            st.plotly_chart(fig_hist_map, width="stretch")
        
    with col_hist2:
        with st.container(border=True):
            st.markdown(f'<div class="chart-title">球場停賽排行前 15 名 ({selected_months_str})</div>', unsafe_allow_html=True)
            
            df_bar_count = df_chart_scope.groupby(["球場名稱", "球隊簡寫"]).size().reset_index(name="總場次")
            df_bar_count["軸標籤"] = df_bar_count["球場名稱"] + " (" + df_bar_count["球隊簡寫"] + ")"
            df_bar_sorted = df_bar_count.sort_values(by="總場次", ascending=False).head(15)
            
            fig_bar = px.bar(
                df_bar_sorted, x="軸標籤", y="總場次",
                color="總場次", color_continuous_scale="Oranges"
            )
            fig_bar.update_layout(
                xaxis=dict(title=None),
                xaxis_tickangle=-45, 
                margin={"r":10,"t":10,"l":10,"b":10},
                height=320,
                coloraxis_colorbar=dict(len=1.0, y=0.5, thickness=15)
            )
            st.plotly_chart(fig_bar, width="stretch")

    # 停賽事件動態觀測細節表
    st.markdown('<div class="chart-title">停賽資訊細節表（隨時間、球隊、月份即時變動）</div>', unsafe_allow_html=True)
    df_table_display = df_table_scope.copy()
    st.dataframe(df_table_display[["年份", "日期", "主場球隊", "對戰組合", "球場名稱", "異常原因"]], width="stretch", hide_index=True)