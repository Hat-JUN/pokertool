import streamlit as st
import pandas as pd
import math
import time

# --- リングゲーム用計算関数 ---
def calculate_ring_game_chip_counts(sb, bb, stack_bb):
    """
    ブラインドとスタックサイズに基づいて、各チップ額面の枚数を計算する。
    BBが大きい場合に、相対的にBBより小さい額面のチップ（特に1ドル）を減らすように調整。
    """
    stack_value = stack_bb * bb

    chip_counts = {
        1: 0,
        5: 0,
        10: 0,
        25: 0,
        # 100以上のチップは、基本は「お釣り/補充用」として計算に含めない
    }

    remaining_value = stack_value

    # 初期割り当て：できるだけ高額チップから割り当てる基本的な方針
    num_25 = min(remaining_value // 25, math.floor(stack_value * 0.4 / 25)) # 最大40%を25ドルに
    chip_counts[25] = max(int(num_25), 0)
    remaining_value -= chip_counts[25] * 25

    num_10 = min(remaining_value // 10, math.floor(stack_value * 0.3 / 10)) # 最大30%を10ドルに
    chip_counts[10] = max(int(num_10), 0)
    remaining_value -= chip_counts[10] * 10

    num_5 = remaining_value // 5
    chip_counts[5] = max(int(num_5), 0)
    remaining_value %= 5

    chip_counts[1] = max(int(remaining_value // 1), 0)
    remaining_value %= 1

    # ここからが重要な調整フェーズ：BBの額面に応じた低額チップの枚数調整

    # 1. 1ドルチップの最低枚数を保証
    if bb <= 2:
        min_1_dollar_chips = 15
    elif bb <= 5:
        min_1_dollar_chips = 8
    else:
        min_1_dollar_chips = 4
        
    if chip_counts[1] < min_1_dollar_chips:
        needed_1s = min_1_dollar_chips - chip_counts[1]
        
        if chip_counts[5] > 0 and (chip_counts[5] * 5 >= needed_1s):
            num_5_to_break = math.ceil(needed_1s / 5)
            actual_5_to_break = min(num_5_to_break, chip_counts[5])
            chip_counts[5] -= actual_5_to_break
            chip_counts[1] += actual_5_to_break * 5
            
        if chip_counts[1] < min_1_dollar_chips:
            needed_1s = min_1_dollar_chips - chip_counts[1]
            if chip_counts[10] > 0 and (chip_counts[10] * 10 >= needed_1s):
                num_10_to_break = math.ceil(needed_1s / 10)
                actual_10_to_break = min(num_10_to_break, chip_counts[10])
                chip_counts[10] -= actual_10_to_break
                chip_counts[1] += actual_10_to_break * 10
                
    # 2. 5ドルチップの最低枚数を保証
    if bb <= 2:
        min_5_dollar_chips = 10
    elif bb <= 5:
        min_5_dollar_chips = 12
    else:
        min_5_dollar_chips = 8
        
    if chip_counts[5] < min_5_dollar_chips:
        needed_5s = min_5_dollar_chips - chip_counts[5]
        if chip_counts[10] > 0 and (chip_counts[10] * 2 >= needed_5s):
            num_10_to_break = math.ceil(needed_5s / 2)
            actual_10_to_break = min(num_10_to_break, chip_counts[10])
            chip_counts[10] -= actual_10_to_break
            chip_counts[5] += actual_10_to_break * 2
            
    current_total_value = sum(k * v for k, v in chip_counts.items())
    if current_total_value != stack_value:
        diff = stack_value - current_total_value
        chip_counts[1] += diff 
        
    for k in chip_counts:
        chip_counts[k] = max(chip_counts[k], 0)

    return {k: v for k, v in chip_counts.items() if v >= 0}

# --- トーナメント用計算関数 ---
def generate_tournament_structure(initial_stack, tournament_type):
    """
    トーナメントの種類と初期スタックに基づいてブラインドストラクチャーを生成する。
    アンティをBBアンティとしてレベル2から導入。
    """
    # 標準的なブラインドレベルの進行 (SB, BB)
    standard_blinds_only = [
        (1, 2), (2, 4), (3, 6), (4, 8), (5, 10),
        (8, 16), (10, 20), (15, 30), (20, 40),
        (25, 50), (30, 60), (40, 80), (50, 100), (60, 120),
        (80, 160), (100, 200), (125, 250), (150, 300), (200, 400),
        (250, 500), (300, 600), (400, 800), (500, 1000), (600, 1200),
        (800, 1600), (1000, 2000)
    ]

    # トーナメントタイプごとのレベル時間 (分)
    level_times = {
        'ロング': 20,
        'ノーマル': 15,
        'ターボ': 10,
        'ハイパーターボ': 6
    }

    structure = []
    level = 1
    
    for sb_val, bb_val in standard_blinds_only:
        ante_val = 0
        if level >= 2: # レベル2からBBアンティを導入
            ante_val = bb_val # BBと同額のアンティ

        # BBが初期スタックの半分を超える、またはスタックがBBの10倍を下回ったら終了
        if (bb_val > initial_stack / 2 and level > 5) or (initial_stack / bb_val < 10 and level > 5):
             break
        
        structure.append({
            "レベル": level,
            "SB": sb_val,
            "BB": bb_val,
            "BBアンティ": ante_val,
            "レベル時間 (分)": level_times[tournament_type]
        })
        level += 1
        
    # もしストラクチャーが短すぎる場合は、最低限のレベルを保証
    if len(structure) < 8 and len(standard_blinds_only) >= 8: # 最低8レベルは保証
        structure = []
        level = 1
        for sb_val, bb_val in standard_blinds_only:
            ante_val = 0
            if level >= 2:
                ante_val = bb_val
            structure.append({
                "レベル": level,
                "SB": sb_val,
                "BB": bb_val,
                "BBアンティ": ante_val,
                "レベル時間 (分)": level_times[tournament_type]
            })
            level += 1
            if level > 8: # 最低8レベルは保証
                break

    return pd.DataFrame(structure)

# --- Streamlit アプリケーションの初期設定と状態管理 ---
st.set_page_config(layout="centered", page_title="ポーカーツール")

# セッション状態の初期化
if 'tournament_structure_df' not in st.session_state:
    st.session_state.tournament_structure_df = pd.DataFrame()
if 'current_level_idx' not in st.session_state:
    st.session_state.current_level_idx = 0
if 'remaining_time_seconds' not in st.session_state:
    st.session_state.remaining_time_seconds = 0
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
if 'initial_stack_for_tournament_set' not in st.session_state:
    st.session_state.initial_stack_for_tournament_set = 1000 # デフォルト値を1000に変更
if 'tournament_type_set' not in st.session_state:
    st.session_state.tournament_type_set = 'ノーマル' # デフォルト値
if 'tournament_format_set' not in st.session_state:
    st.session_state.tournament_format_set = '通常' # デフォルト値
if 'game_mode_set' not in st.session_state: # トーナメント用ゲームモード
    st.session_state.game_mode_set = 'ノーリミットホールデム' # デフォルト値
if 'entries' not in st.session_state:
    st.session_state.entries = 10 # デフォルト値
if 'remaining_players' not in st.session_state:
    st.session_state.remaining_players = 10 # デフォルト値
if 'pickem_game_mode' not in st.session_state: # ピッケム用ゲームモード
    st.session_state.pickem_game_mode = 'テキサスホールデム' # デフォルト値

# --- サイドバーでページ選択 ---
st.sidebar.title("ツール選択")
page_selection = st.sidebar.radio(
    "表示するツールを選択してください:",
    ("リングゲーム チップ構成", "トーナメント ブラインドストラクチャー", "トーナメントタイマー", "ピッケム") # ピッケムを追加
)

# --- 各ページの表示ロジック ---
if page_selection == "リングゲーム チップ構成":
    st.title('ポーカーリングゲーム チップ構成計算ツール')
    st.write('ブラインドとスタックサイズを入力すると、人数に応じたおすすめのチップ枚数を計算します。')

    st.header('設定')

    col1, col2, col3 = st.columns(3)

    with col1:
        sb = st.number_input('スモールブラインド (SB)', min_value=1, value=1, step=1)
    with col2:
        bb = st.number_input('ビッグブラインド (BB)', min_value=1, value=2, step=1)
        if bb <= sb:
            st.error('ビッグブラインドはスモールブラインドより大きくしてください。')
            st.stop()
    with col3:
        stack_bb = st.number_input('初期スタックサイズ (BB)', min_value=50, value=200, step=10)

    st.header('計算結果')

    player_chip_counts = calculate_ring_game_chip_counts(sb, bb, stack_bb)
    player_stack_value = stack_bb * bb

    st.subheader(f'各プレイヤーへの配布チップ（合計 {player_stack_value} ドル / {stack_bb} BB）')

    player_df_data = [{"額面 (ドル)": chip, "枚数": count}
                      for chip, count in player_chip_counts.items() if count > 0]
    if player_df_data:
        player_df = pd.DataFrame(player_df_data)
        st.dataframe(player_df, hide_index=True, use_container_width=True)
    else:
        st.write("選択された設定ではチップを割り当てることができませんでした。スタックサイズやブラインドを見直してください。")


    st.subheader('人数ごとの必要チップ枚数')

    num_players = list(range(2, 10))
    data = []

    for num in num_players:
        row = {"参加人数": f"{num}人"}
        total_row_chips = 0
        for chip_value in [1, 5, 10, 25, 100, 500, 1000]:
            count = player_chip_counts.get(chip_value, 0)
            total_count = count * num
            row[f'{chip_value}ドル'] = total_count
            total_row_chips += total_count
        row["総チップ枚数"] = total_row_chips
        data.append(row)

    temp_df = pd.DataFrame(data)

    cols_to_keep = ['参加人数', '総チップ枚数']
    for col in temp_df.columns:
        if 'ドル' in col and not (temp_df[col] == 0).all():
            cols_to_keep.append(col)

    sorted_cols_to_keep = sorted([c for c in cols_to_keep if 'ドル' in c], key=lambda x: int(x.replace('ドル', '')))
    final_cols_order = ['参加人数'] + sorted_cols_to_keep + ['総チップ枚数']

    total_chips_df = temp_df[final_cols_order]

    st.dataframe(total_chips_df, hide_index=True, use_container_width=True)

    st.write("---")
    st.write("**補足事項 (リングゲーム):**")
    st.write("1. **高額チップの扱い:** 上記の計算では、100ドル以上の高額チップは基本的には含んでいません。これらのチップは、ゲーム中にチップの交換（ブレイク）や補充が必要になった際に利用することを推奨します。")
    st.write("2. **低額チップの調整:** ビッグブラインド (BB) の額面に応じて、1ドルや5ドルのチップの最低枚数を調整しています。BBが大きくなるほど、**BB未満のチップ（特に1ドル）の枚数は少なくなる傾向**にあります。")
    st.write("3. **チップセットの調整:** この構成はあくまで推奨値です。お手持ちのチップセットの実際の枚数や額面構成に合わせて、適宜調整してください。")
    st.write("4. **端数処理:** 計算の都合上、枚数に端数が出た場合は最も小さい額面（1ドルチップ）で調整しています。")

elif page_selection == "トーナメント ブラインドストラクチャー":
    st.title('ポーカー トーナメント ブラインドストラクチャー作成ツール')
    st.write('初期スタックサイズ、ブラインドスピード、トーナメント形式、ゲームモードを選択すると、推奨されるブラインドストラクチャーを生成します。')

    st.header('設定')

    col1, col2, col3 = st.columns(3)
    with col1:
        initial_stack_for_tournament_input = st.number_input(
            '初期スタックサイズ (チップ点数)', 
            min_value=200, 
            value=st.session_state.initial_stack_for_tournament_set, 
            step=100,
            key="initial_stack_input" 
        )
    with col2:
        tournament_type_input = st.selectbox(
            'ブラインドスピード', 
            ('ロング', 'ノーマル', 'ターボ', 'ハイパーターボ'),
            index=('ロング', 'ノーマル', 'ターボ', 'ハイパーターボ').index(st.session_state.tournament_type_set),
            key="tournament_type_select"
        )
    with col3:
        tournament_format_input = st.selectbox(
            'トーナメント形式',
            ('通常', 'ノックアウト (KO)', 'プログレッシブノックアウト (PKO)'),
            index=('通常', 'ノックアウト (KO)', 'プログレッシブノックアウト (PKO)').index(st.session_state.tournament_format_set),
            key="tournament_format_select"
        )
    
    game_mode_input = st.selectbox(
        'ゲームモード',
        ('ノーリミットホールデム', 'オマハ', 'スプリットホールデム'),
        index=('ノーリミットホールデム', 'オマハ', 'スプリットホールデム').index(st.session_state.game_mode_set),
        key="game_mode_select"
    )

    if st.button('ストラクチャー確定', key='generate_structure_btn'):
        st.session_state.initial_stack_for_tournament_set = initial_stack_for_tournament_input
        st.session_state.tournament_type_set = tournament_type_input
        st.session_state.tournament_format_set = tournament_format_input
        st.session_state.game_mode_set = game_mode_input
        st.session_state.tournament_structure_df = generate_tournament_structure(
            st.session_state.initial_stack_for_tournament_set, 
            st.session_state.tournament_type_set
        )
        st.session_state.current_level_idx = 0
        if not st.session_state.tournament_structure_df.empty:
            current_level_data = st.session_state.tournament_structure_df.iloc[st.session_state.current_level_idx]
            st.session_state.remaining_time_seconds = current_level_data['レベル時間 (分)'] * 60
        else:
            st.session_state.remaining_time_seconds = 0
        st.session_state.timer_running = False 

        st.success('ブラインドストラクチャーが確定されました！「トーナメントタイマー」ページへ移動してスタートできます。')
        st.rerun() 

    st.header('ブラインドストラクチャー')

    if not st.session_state.tournament_structure_df.empty:
        st.dataframe(st.session_state.tournament_structure_df, hide_index=True, use_container_width=True)
    else:
        st.write("上記の設定を行い、「ストラクチャー確定」ボタンを押してください。")

    st.write("---")
    st.write("**補足事項 (トーナメント):**")
    st.write("1. **BBアンティ:** このストラクチャーでは、**レベル2からBBアンティ（ビッグブラインドと同額のアンティ）が導入**されます。BBアンティは、ビッグブラインドを支払うプレイヤーが、自分自身のビッグブラインドに加えてアンティもまとめて支払う形式です。これにより、ゲームの進行がスムーズになります。")
    st.write("2. **ブラインドスピードの目安:**") 
    st.write("   - **ロング:** 各レベル20分以上。じっくりと戦略を練りたい場合に適しています。")
    st.write("   - **ノーマル:** 各レベル15分程度。最も一般的なトーナメントの進行速度です。")
    st.write("   - **ターボ:** 各レベル10分程度。比較的短い時間で決着がつくため、カジュアルなプレイに適しています。")
    st.write("   - **ハイパーターボ:** 各レベル5-6分程度。非常にスピーディーな展開で、運の要素も大きくなります。")
    st.write("3. **トーナメント形式:**") 
    st.write("   - **通常:** 標準的なトーナメント形式。")
    st.write("   - **ノックアウト (KO):** プレイヤーを飛ばすと、そのプレイヤーに設定されたバウンティ（賞金）の一部または全部を獲得できます。")
    st.write("   - **プログレッシブノックアウト (PKO):** ノックアウトと同様にバウンティを獲得できますが、獲得したバウンティの一部が自分自身のバウンティに加算され、頭上に乗るバウンティが増えていきます。")
    st.write("4. **ゲームモード:**") 
    st.write("   - **ノーリミットホールデム:** 最も一般的なポーカー形式で、ベットに上限がありません。")
    st.write("   - **オマハ:** プレイヤーに4枚のホールカードが配られ、ボードの3枚と手札の2枚を組み合わせて役を作ります。")
    st.write("   - **スプリットホールデム:** 通常のホールデムに加え、ポットを最も低い役と最も高い役で分割する形式です。")
    st.write("5. **スタックの深さ:** 生成されるブラインドレベルは、初期スタックサイズに対して極端に浅くならないように調整されています。プレイヤーが一定のBB数を維持できるレベルまでを推奨しています。")
    st.write("6. **ブレイク:** 通常、トーナメントでは数レベルごとに休憩（ブレイク）が入ります。この表には含まれていませんが、実際の運用では適宜ブレイクを設けることをお勧めします。")

elif page_selection == "トーナメントタイマー":
    if st.session_state.tournament_structure_df.empty:
        st.warning('まず「トーナメント ブラインドストラクチャー」ページでストラクチャーを確定してください。')
        st.stop()

    df = st.session_state.tournament_structure_df
    current_level_idx = st.session_state.current_level_idx
    total_levels = len(df)

    # 現在のレベル情報を取得
    if current_level_idx < total_levels:
        current_level_data = df.iloc[current_level_idx]
    else:
        st.info("全てのレベルが終了しました！お疲れ様でした！")
        st.session_state.timer_running = False
        current_level_data = {
            "レベル": "終了", "SB": "-", "BB": "-", "BBアンティ": "-", "レベル時間 (分)": 0
        }

    

    # === エントリー人数、残り人数、平均スタックの入力と表示 ===
    st.subheader("現在の参加状況")
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.session_state.entries = st.number_input(
            'エントリー人数', min_value=1, value=st.session_state.entries, step=1, key='entries_input'
        )
    with col_info2:
        st.session_state.remaining_players = st.number_input(
            '残り人数', 
            min_value=1, 
            max_value=st.session_state.entries, 
            value=min(st.session_state.remaining_players, st.session_state.entries), 
            step=1, 
            key='remaining_players_input'
        )
    with col_info3:
        initial_stack_val = st.session_state.initial_stack_for_tournament_set
        avg_stack = 0
        if st.session_state.remaining_players > 0:
            avg_stack = (st.session_state.entries * initial_stack_val) / st.session_state.remaining_players
        st.metric("平均スタック", f"{int(avg_stack)}")
    st.markdown("---")


    st.header(f'現在のレベル: {current_level_data["レベル"]}')
    st.subheader(f'SB: {current_level_data["SB"]} / BB: {current_level_data["BB"]} / BBアンティ: {current_level_data["BBアンティ"]}')

    # 次のレベルの表示
    st.markdown("---")
    if current_level_idx + 1 < total_levels:
        next_level_data = df.iloc[current_level_idx + 1]
        st.markdown(f"""
        <div style="text-align: center; font-size: 24px; color: gray;">
            次のレベル: {next_level_data["レベル"]} (SB: {next_level_data["SB"]} / BB: {next_level_data["BB"]} / BBアンティ: {next_level_data["BBアンティ"]})
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="text-align: center; font-size: 24px; color: gray;">
            次のレベルはありません (最終レベル)
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")


    # タイマー表示部分
    time_display_placeholder = st.empty()

    # コントロールボタン
    col_controls1, col_controls2, col_controls3 = st.columns(3)
    with col_controls1:
        if st.button('◀️ 1分戻す'):
            st.session_state.remaining_time_seconds = max(0, st.session_state.remaining_time_seconds + 60)
            st.rerun()
        if st.button('◀️ 1レベル戻す'):
            if st.session_state.current_level_idx > 0:
                st.session_state.current_level_idx -= 1
                new_level_data = df.iloc[st.session_state.current_level_idx]
                st.session_state.remaining_time_seconds = new_level_data['レベル時間 (分)'] * 60
                st.session_state.timer_running = False # レベル変更時は一旦停止
                st.rerun()
            else:
                st.warning("これ以上戻るレベルはありません。")
    with col_controls2:
        if st.button('▶️ 1分進む'):
            st.session_state.remaining_time_seconds = max(0, st.session_state.remaining_time_seconds - 60)
            if st.session_state.remaining_time_seconds <= 0 and st.session_state.current_level_idx < total_levels -1:
                st.session_state.current_level_idx += 1
                next_level_data = df.iloc[st.session_state.current_level_idx]
                st.session_state.remaining_time_seconds = next_level_data['レベル時間 (分)'] * 60
            st.rerun()
        if st.button('▶️ 1レベル進む'):
            if st.session_state.current_level_idx < total_levels - 1:
                st.session_state.current_level_idx += 1
                next_level_data = df.iloc[st.session_state.current_level_idx]
                st.session_state.remaining_time_seconds = next_level_data['レベル時間 (分)'] * 60
                st.session_state.timer_running = False # レベル変更時は一旦停止
                st.rerun()
            else:
                st.warning("これ以上進むレベルはありません。")
    with col_controls3:
        if st.session_state.timer_running:
            if st.button('⏸️ タイマー停止'):
                st.session_state.timer_running = False
                st.rerun()
        else:
            if st.button('▶️ タイマー開始'):
                st.session_state.timer_running = True
                st.rerun()
    # === トーナメント情報（初期スタック、ブラインドスピード、バウンティオプション、ゲームモード）の表示 ===
    st.subheader("トーナメント概要")
    col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
    with col_summary1:
        st.markdown(f"**ゲームモード:** {st.session_state.game_mode_set}") # ゲームモードを表示
    with col_summary2:
        st.markdown(f"**初期スタック:** {st.session_state.initial_stack_for_tournament_set}点")
    with col_summary3:
        st.markdown(f"**ブラインドスピード:** {st.session_state.tournament_type_set}")
    with col_summary4:
        if st.session_state.tournament_format_set != '通常':
            st.markdown(f"**バウンティオプション:** {st.session_state.tournament_format_set}")
        else:
            st.markdown(f"**バウンティオプション:** なし")
    st.markdown("---")


    # タイマーロジック
    if st.session_state.timer_running and current_level_idx < total_levels:
        with time_display_placeholder:
            while st.session_state.remaining_time_seconds > 0 and st.session_state.timer_running:
                mins, secs = divmod(st.session_state.remaining_time_seconds, 60)
                time_str = f"残り時間: {int(mins):02d}:{int(secs):02d}"
                st.markdown(f"<h1 style='text-align: center; font-size: 72px;'>{time_str}</h1>", unsafe_allow_html=True)
                time.sleep(1)
                st.session_state.remaining_time_seconds -= 1
                st.rerun()
            
            if st.session_state.remaining_time_seconds <= 0 and st.session_state.current_level_idx < total_levels -1:
                st.session_state.current_level_idx += 1
                st.session_state.timer_running = False
                st.info(f"レベル {current_level_data['レベル']} が終了しました！次のレベルへ進みます。")
                
                next_level_data = df.iloc[st.session_state.current_level_idx]
                st.session_state.remaining_time_seconds = next_level_data['レベル時間 (分)'] * 60
                st.rerun()
            elif st.session_state.remaining_time_seconds <= 0 and st.session_state.current_level_idx == total_levels -1:
                st.info("全てのレベルが終了しました！")
                st.session_state.timer_running = False
                st.rerun()

    elif current_level_idx < total_levels:
        mins, secs = divmod(st.session_state.remaining_time_seconds, 60)
        time_str = f"残り時間: {int(mins):02d}:{int(secs):02d}"
        time_display_placeholder.markdown(f"<h1 style='text-align: center; font-size: 72px;'>{time_str}</h1>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("今後のブラインドレベル")
    if current_level_idx < total_levels:
        st.dataframe(df.iloc[current_level_idx:].reset_index(drop=True), hide_index=True, use_container_width=True)
    else:
        st.write("全てのブラインドレベルが表示されました。")

# --- ピッケムページ ---
elif page_selection == "ピッケム":
    st.title('ピッケム')
    st.write('プレイしたいゲームモードを選択してください。')

    # ピッケム用のゲームモード選択肢を更新
    # アスタリスク付きのゲームは除外
    pickem_game_mode_options = [
        'Holdem - Normal',
        'Holdem - Super', # 一般的なゲームとして追加
        'Drawmaha - Hi',
        'Drawmaha - 27 lowball',
        'Drawmaha - A5 lowball',
        'Drawmaha - Badugi',
        'Drawmaha - Hi-dugi',
        'Drawmaha - 0',
        'Drawmaha - 49',
        'Draw - 27 lowball',
        'Draw - A5 lowball',
        'Draw - Badugi', # DrawmahaのBadugiと区別するためカテゴリ名を追加
        'Draw - Hi-dugi', # DrawmahaのHi-dugiと区別するためカテゴリ名を追加
        'Draw - Badacey',
        'Draw - Badeucey',
        'Draw - Archie',
        'Omaha - Double Board Hi/Hi (4 or 5枚)',
        'Omaha - Double Board Best/Best (4 or 5枚)'
    ]

    st.session_state.pickem_game_mode = st.selectbox(
        'ゲームモードを選択',
        pickem_game_mode_options,
        index=pickem_game_mode_options.index(st.session_state.pickem_game_mode) if st.session_state.pickem_game_mode in pickem_game_mode_options else 0,
        key="pickem_game_mode_select"
    )

    st.markdown("---")
    st.subheader("現在選択中のゲーム")
    st.markdown(f"<h1 style='text-align: center; font-size: 48px; color: #4CAF50;'>{st.session_state.pickem_game_mode}</h1>", unsafe_allow_html=True)

    st.write("このページでは、選択されたゲームモードが表示されます。")
    st.write("今後、選択されたゲームモードに応じた情報や機能を追加する予定です。")