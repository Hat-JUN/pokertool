import streamlit as st
import pandas as pd
import os
import datetime

# CSVファイルのパスを定義
DATA_FILE = 'poker_sessions.csv'
st.set_page_config(
    page_title="ROItool",
    page_icon=":1234:" # ここでアイコンを指定
)
# --- データの読み込みと初期化 ---
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=['日付', 'バイイン', '賞金', '純利益', 'ROI'])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

if 'sessions' not in st.session_state:
    st.session_state.sessions = load_data()
    # データを日付の降順（新しいものが上）にソートして保存
    if not st.session_state.sessions.empty:
        st.session_state.sessions = st.session_state.sessions.sort_values(by='日付', ascending=False, ignore_index=True)

# --- アプリケーションのUI ---
st.title('ポーカーROIトラッカー')
st.write('ポーカーセッションのROIを記録しましょう！')

# フォームの作成
with st.form("session_form"):
    st.subheader("新しいセッションの追加")
    # デフォルトで今日の日付を設定
    date = st.date_input("日付", value=datetime.date.today())
    buy_in = st.number_input("バイイン（円）", min_value=0)
    payout = st.number_input("賞金（円）", min_value=0)
    submitted = st.form_submit_button("セッションを追加")

    if submitted:
        if buy_in <= 0:
            st.error("バイインは0より大きい値を入力してください。")
        else:
            net_profit = payout - buy_in
            roi = (net_profit / buy_in) * 100
            new_session = pd.DataFrame([{
                '日付': date,
                'バイイン': buy_in,
                '賞金': payout,
                '純利益': net_profit,
                'ROI': roi
            }])
            # 新しいセッションデータを追加し、日付でソート
            st.session_state.sessions = pd.concat([st.session_state.sessions, new_session], ignore_index=True)
            st.session_state.sessions = st.session_state.sessions.sort_values(by='日付', ascending=False, ignore_index=True)
            # データをCSVに保存
            save_data(st.session_state.sessions)

# --- 計算結果の表示 ---
if not st.session_state.sessions.empty:
    st.subheader("全体の結果")
    total_buy_in = st.session_state.sessions['バイイン'].sum()
    total_payout = st.session_state.sessions['賞金'].sum()
    total_net_profit = total_payout - total_buy_in
    if total_buy_in > 0:
        overall_roi = (total_net_profit / total_buy_in) * 100
    else:
        overall_roi = 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総バイイン", f"{total_buy_in:,.0f}円")
    col2.metric("総賞金", f"{total_payout:,.0f}円")
    col3.metric("総純利益", f"{total_net_profit:,.0f}円")
    col4.metric("全体ROI", f"{overall_roi:.2f}%")

    # --- グラフの表示 ---
    st.subheader("ROIの推移")
    st.line_chart(st.session_state.sessions['ROI'])
    
    # --- 履歴の表示と削除機能 ---
    st.subheader("セッション履歴（削除可能）")
    st.write("削除したい行の左側にあるチェックボックスにチェックを入れ、[Delete]ボタンを押してください。")
    
    edited_df = st.data_editor(
        st.session_state.sessions, 
        num_rows="dynamic",
        use_container_width=True
    )
    
    if st.button("削除を確定"):
        st.session_state.sessions = edited_df
        save_data(st.session_state.sessions)
        st.success("履歴が更新されました。")

else:
    st.info("まだセッションがありません。上のフォームから最初のセッションを追加してください。")