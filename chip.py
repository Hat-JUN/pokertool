import streamlit as st
import pandas as pd
import math
import time

# --- ゲームルール辞書 ---
game_rules = {
    'Holdem - Normal': """
    **Holdem - Normalのルール:**
    * 各プレイヤーに2枚のホールカードが配られます。
    * コミュニティカードとして5枚のカードがボードに公開されます。
    * プレイヤーは、手札2枚とボードの5枚の中から任意の5枚を組み合わせて最も強い役を作ります。
    * ベットラウンドは、プリフロップ、フロップ、ターン、リバーの計4回あります。
    """,
    'Holdem - Super': """
    **Holdem - Superのルール:**
    * 各プレイヤーに3枚のホールカードが配られます。
    * コミュニティカードとして5枚のカードがボードに公開されます。
    * プレイヤーは、手札3枚の中から**必ず2枚**と、ボードの5枚の中から任意の3枚を組み合わせて最も強い役を作ります。
    * ベットラウンドは、プリフロップ、フロップ、ターン、リバーの計4回あります。
    """,
    'Drawmaha - Hi': """
    **Drawmaha - Hiのルール:**
    * オマハホールデムとファイブカードドローを組み合わせたゲームで、ハイハンドのみで勝敗を競います。
    * プレイヤーは、4枚の手札と5枚のコミュニティカードを使います。
    * コミュニティカードが公開される前に、手札の一部を交換（ドロー）することができます。
    """,
    'Drawmaha - 27 lowball': """
    **Drawmaha - 27 lowballのルール:**
    * オマハホールデムとドローポーカーを組み合わせたゲームで、2-7ローボールのルールで勝敗を競います。
    * 2-7ローボールでは、ストレートやフラッシュはローハンドの妨げになり、エースはハイカードとして扱われます。
    * ポットは最も低い役のプレイヤーが獲得します。
    """,
    'Drawmaha - A5 lowball': """
    **Drawmaha - A5 lowballのルール:**
    * オマハホールデムとドローポーカーを組み合わせたゲームで、A-5ローボールのルールで勝敗を競います。
    * A-5ローボールでは、ストレートやフラッシュはローハンドの妨げにならず、エースは最も弱いカード（ローカード）として扱われます。
    * ポットは最も低い役のプレイヤーが獲得します。
    """,
    'Drawmaha - Badugi': """
    **Drawmaha - Badugiのルール:**
    * オマハホールデムとファイブカードドローを組み合わせたゲームで、バドゥギハンドのみで勝敗を競います。
    * バドゥギとは、スートもランクも重複しない4枚のカードで構成される役です。最も強いバドゥギが勝ちとなります。
    """,
    'Drawmaha - Hi-dugi': """
    **Drawmaha - Hi-dugiのルール:**
    * 4枚の手札で役の強さを競う、バドゥーギの亜種です。
    * **ルール:** スートの重複は禁止されますが、**数字の重複は許されます**。
    * **役の強さ（ハイハンド）:** ハイカード < ワンペア < ツーペア < スリーカード < フォーカード の順に強くなります。
    * 5枚役（ストレート、フラッシュ）はありません。AはKよりも強いカードです。
    * 最強の役は、スートが全て異なるA4枚のフォーカード（AAAA）です。
    * 最弱の役は、スートが全て異なる2, 3, 4, 5のハイカードです。
    """,
    'Drawmaha - 0': """
    **Drawmaha - 0のルール:**
    * オマハホールデムとファイブカードドローを組み合わせたゲームで、手札の数値が低い人が勝利となります。
    * ナッツ（最強の役）はオールピクチャー（K, Q, J, T）で構成される役となります。
    """,
    'Drawmaha - 49': """
    **Drawmaha - 49のルール:**
    * オマハホールデムとファイブカードドローを組み合わせたゲームで、手札の数値が高いプレイヤーが勝利となります。
    * ピクチャーカードは0扱いとなります。
    * ナッツ（最強の役）はTTTT9となります。
    """,
    'Draw - Hi': """
    **Draw - Hiのルール:**
    * プレイヤーに配られた手札の交換（ドロー）によって、通常のポーカーの最も強い役（ハイハンド）を目指すゲームです。
    * コミュニティカードは使用しません。
    """,
    'Draw - 27 lowball': """
    **Draw - 27 lowballのルール:**
    * 5枚の手札が配られ、ドローラウンドで手札を交換できるドローポーカーです。
    * 2-7ローボールのルールで勝敗を競います。ストレートやフラッシュはローハンドの妨げになり、エースはハイカードとして扱われます。
    * ポットは最も低い役のプレイヤーが獲得します。
    """,
    'Draw - A5 lowball': """
    **Draw - A5 lowballのルール:**
    * 5枚の手札が配られ、ドローラウンドで手札を交換できるドローポーカーです。
    * A-5ローボールのルールで勝敗を競います。ストレートやフラッシュはローハンドの妨げにならず、エースは最も弱いカードとして扱われます。
    * ポットは最も低い役のプレイヤーが獲得します。
    """,
    'Draw - Badugi': """
    **Draw - Badugiのルール:**
    * バドゥギハンド（スートとランクが重複しない4枚のカード）のみで勝敗を競うドローポーカーです。
    * 各プレイヤーに4枚の手札が配られ、ドローラウンドで手札を交換できます。
    """,
    'Draw - Hi-dugi': """
    **Draw - Hi-dugiのルール:**
    * 4枚の手札で役の強さを競う、バドゥーギの亜種です。
    * **ルール:** スートの重複は禁止されますが、**数字の重複は許されます**。
    * **役の強さ（ハイハンド）:** ハイカード < ワンペア < ツーペア < スリーカード < フォーカード の順に強くなります。
    * 5枚役（ストレート、フラッシュ）はありません。AはKよりも強いカードです。
    * 最強の役は、スートが全て異なるA4枚のフォーカード（AAAA）です。
    * 最弱の役は、スートが全て異なる2, 3, 4, 5のハイカードです。
    """,
    'Draw - Badacey': """
    **Draw - Badaceyのルール:**
    * バドゥギハンドとエースを最も強いカードとするローハンドでポットを分け合うドローポーカーです。
    * ドローラウンドで手札を交換し、ショーダウン時に勝敗が決まります。
    """,
    'Draw - Badeucey': """
    **Draw - Badeuceyのルール:**
    * バドゥギハンドと2を最も強いカードとするローハンドでポットを分け合うドローポーカーです。
    * ルールはBadaceyに似ていますが、ローハンドのカウント方法が異なります。
    """,
    'Draw - Archie': """
    **Draw - Archieのルール:**
    * ハイハンドとバドゥギハンドでポットを分け合うドローポーカーで、手札は5枚配られます。
    * コミュニティカードがないため、より純粋なドローの戦略が求められます。
    """,
    'Omaha - Double Board Hi/Hi (4 or 5枚)': """
    **Omaha - Double Board Hi/Hi (4 or 5枚)のルール:**
    * 2つの異なるボード（コミュニティカード）が用意されるオマハです。
    * プレイヤーは、それぞれのボードで最も強いハイハンドを作ります。
    * 2つのボードそれぞれの勝者がポットを分け合います。
    """,
    'Omaha - Double Board Best/Best (4 or 5枚)': """
    **Omaha - Double Board Best/Best (4 or 5枚)のルール:**
    * 2つの異なるボードが用意されるオマハで、ハイハンドとローハンドでポットを分け合います。
    * 各ボードで最も強い役（ハイハンド）と最も低い役（ローハンド）を作り、それぞれでポットを分け合います。
    """,
    'Stud - Super Stud': """
    **Stud - Super Studのルール:**
    * ゲームはセブンカードスタッド形式で進行します。
    * 最初にプレイヤーには4枚のホールカードが配られます。
    * その中から2枚を破棄（ディスカード）し、残された2枚の手札でゲームをプレイします。
    """,
    'Stud - Super Stud H/L8': """
    **Stud - Super Stud H/L8のルール:**
    * ゲームはセブンカードスタッドのハイ/ロースプリット（H/L8）形式で進行します。
    * 最初にプレイヤーには4枚のホールカードが配られ、その中から2枚を破棄（ディスカード）します。
    * 7枚の最終手札の中からベストな5枚を使用して、最高のハイハンドと、8以下のカードで構成された最高のローハンド（A-5ルール）を競い、ポットをスプリットします。
    * ローハンドとして認められるには、8以下のカード（Aを含む）のみで役を構成する必要があります。
    """
}


# --- リングゲーム用計算関数 ---
def calculate_ring_game_chip_counts(sb, bb, stack_bb):
    stack_value = stack_bb * bb
    all_denominations = [1, 5, 10, 25, 100, 500, 1000]

    min_chip_value = 1
    if sb >= 25:
        min_chip_value = 25
    elif sb >= 5:
        min_chip_value = 5
    
    try:
        start_index = all_denominations.index(min_chip_value)
        if start_index + 4 > len(all_denominations):
            selected_denominations = all_denominations[-4:]
        else:
            selected_denominations = all_denominations[start_index : start_index + 4]
    except ValueError:
        if sb > 25:
            selected_denominations = [25, 100, 500, 1000]
        else:
             selected_denominations = [1, 5, 10, 25]

    chip_counts = {chip: 0 for chip in selected_denominations}
    remaining_value = stack_value
    
    # 新しい割り当てロジック:
    # 1. 最小額面のチップに目標枚数を割り当てる
    # 2. 残りの金額を高額チップから割り当てる
    
    # 1. 各チップ額面の目標枚数を設定し、割り当てる
    target_counts = {
        1: 20, # SB=1ならこの枚数からスタート
        5: 15, # SB=5ならこの枚数からスタート
        10: 10,
        25: 6,
    }
    
    for chip in selected_denominations:
        if chip in target_counts:
            # スタック総額から目標枚数分の金額を割り当てる
            count = min(target_counts[chip], remaining_value // chip)
            chip_counts[chip] = count
            remaining_value -= count * chip
        
    # 2. 残りの金額を最も高い額面のチップに割り当てる
    for chip in sorted(selected_denominations, reverse=True):
        count = remaining_value // chip
        chip_counts[chip] += count
        remaining_value %= chip
        
    # 3. 最終的な端数を最も小さいチップに加算する
    if remaining_value > 0 and min(selected_denominations) in chip_counts:
        chip_counts[min(selected_denominations)] += remaining_value
    
    # 4. 枚数が最大20枚を超えないように調整（前回のロジックを改良）
    for i in range(len(selected_denominations) - 1):
        chip = selected_denominations[i]
        next_chip = selected_denominations[i+1]
        
        # 20枚を超えた分を上位チップにまとめる
        if chip_counts[chip] > 20:
            excess_value = (chip_counts[chip] - 20) * chip
            chip_counts[chip] = 20
            
            count_to_add_next = excess_value // next_chip
            chip_counts[next_chip] += count_to_add_next
            
            # 余りを再度小さいチップに加算
            remaining_after_consolidation = excess_value % next_chip
            if remaining_after_consolidation > 0:
                chip_counts[chip] += remaining_after_consolidation // chip

    return {chip: count for chip, count in chip_counts.items() if count > 0}

# --- トーナメント用計算関数 ---
def generate_tournament_structure(initial_stack, tournament_type):
    standard_blinds_only = [
        (1, 2), (2, 4), (3, 6), (4, 8), (5, 10),
        (8, 16), (10, 20), (15, 30), (20, 40),
        (25, 50), (30, 60), (40, 80), (50, 100), (60, 120),
        (80, 160), (100, 200), (125, 250), (150, 300), (200, 400),
        (250, 500)
    ]
    level_times = {
        'ロング': 20, 'ノーマル': 15, 'ターボ': 10, 'ハイパーターボ': 6
    }
    structure = []
    level = 1
    for sb_val, bb_val in standard_blinds_only:
        ante_val = 0
        if level >= 2: ante_val = bb_val
        structure.append({
            "レベル": level, "SB": sb_val, "BB": bb_val, "BBアンティ": ante_val, "レベル時間 (分)": level_times[tournament_type]
        })
        level += 1
    if len(structure) < 8 and len(standard_blinds_only) >= 8:
        structure = []
        level = 1
        for sb_val, bb_val in standard_blinds_only:
            ante_val = 0
            if level >= 2: ante_val = bb_val
            structure.append({
                "レベル": level, "SB": sb_val, "BB": bb_val, "BBアンティ": ante_val, "レベル時間 (分)": level_times[tournament_type]
            })
            level += 1
            if level > 8: break
    return pd.DataFrame(structure)

# --- Streamlit アプリケーションの初期設定と状態管理 ---
st.set_page_config(layout="centered", page_title="ポーカーツール")

# セッション状態の初期化
if 'tournament_structure_df' not in st.session_state: st.session_state.tournament_structure_df = pd.DataFrame()
if 'current_level_idx' not in st.session_state: st.session_state.current_level_idx = 0
if 'remaining_time_seconds' not in st.session_state: st.session_state.remaining_time_seconds = 0
if 'timer_running' not in st.session_state: st.session_state.timer_running = False
if 'initial_stack_for_tournament_set' not in st.session_state: st.session_state.initial_stack_for_tournament_set = 1000
if 'tournament_type_set' not in st.session_state: st.session_state.tournament_type_set = 'ノーマル'
if 'tournament_format_set' not in st.session_state: st.session_state.tournament_format_set = '通常'
if 'game_mode_set' not in st.session_state: st.session_state.game_mode_set = 'ノーリミットホールデム'
if 'entries' not in st.session_state: st.session_state.entries = 10
if 'remaining_players' not in st.session_state: st.session_state.remaining_players = 10
if 'pickem_game_mode' not in st.session_state: st.session_state.pickem_game_mode = 'Holdem - Normal'

# --- サイドバーでページ選択 ---
st.sidebar.title("ツール選択")
page_selection = st.sidebar.radio(
    "表示するツールを選択してください:",
    ("リングゲーム チップ構成", "トーナメント ブラインドストラクチャー", "トーナメントタイマー", "ピッケム")
)

# --- 各ページの表示ロジック ---
if page_selection == "リングゲーム チップ構成":
    st.title('ポーカーリングゲーム チップ構成計算ツール')
    st.write('ブラインドとスタックサイズを入力すると、SBが支払える最小額から始まる4種類のチップ構成を計算します。')
    st.header('設定')
    col1, col2, col3 = st.columns(3)
    with col1: sb = st.number_input('スモールブラインド (SB)', min_value=1, value=1, step=1)
    with col2:
        bb = st.number_input('ビッグブラインド (BB)', min_value=1, value=2, step=1)
        if bb <= sb: st.error('ビッグブラインドはスモールブラインドより大きくしてください。'); st.stop()
    with col3: stack_bb = st.number_input('初期スタックサイズ (BB)', min_value=50, value=200, step=10)
    st.header('計算結果')
    player_chip_counts = calculate_ring_game_chip_counts(sb, bb, stack_bb)
    player_stack_value = stack_bb * bb
    st.subheader(f'各プレイヤーへの配布チップ（合計 {player_stack_value} ドル / {stack_bb} BB）')
    player_df_data = [{"額面 (ドル)": chip, "枚数": count} for chip, count in player_chip_counts.items() if count > 0]
    if player_df_data: st.dataframe(pd.DataFrame(player_df_data), hide_index=True, use_container_width=True)
    else: st.write("選択された設定ではチップを割り当てることができませんでした。スタックサイズやブラインドを見直してください。")
    st.subheader('人数ごとの必要チップ枚数')
    num_players = list(range(2, 10))
    data = []
    used_denominations = sorted(player_chip_counts.keys())
    for num in num_players:
        row = {"参加人数": f"{num}人"}
        total_row_chips = 0
        for chip_value in used_denominations:
            count = player_chip_counts.get(chip_value, 0)
            total_count = count * num
            row[f'{chip_value}ドル'] = total_count
            total_row_chips += total_count
        row["総チップ枚数"] = total_row_chips
        data.append(row)
    temp_df = pd.DataFrame(data)
    cols_to_keep = ['参加人数'] + [f'{chip}ドル' for chip in used_denominations] + ['総チップ枚数']
    total_chips_df = temp_df[cols_to_keep]
    st.dataframe(total_chips_df, hide_index=True, use_container_width=True)
    st.write("---")
    st.write("**補足事項 (リングゲーム):**")
    st.write("1. **チップ構成:** この計算では、スモールブラインドが支払える最小額のチップから始まる4種類のチップを使用するようにしています。これにより、ゲームの規模に応じた適切なチップ構成を提案します。")
    st.write("2. **端数処理:** 計算の都合上、枚数に端数が出た場合は最も小さい額面チップで調整しています。")

elif page_selection == "トーナメント ブラインドストラクチャー":
    st.title('ポーカー トーナメント ブラインドストラクチャー作成ツール')
    st.write('初期スタックサイズ、ブラインドスピード、トーナメント形式、ゲームモードを選択すると、推奨されるブラインドストラクチャーを生成します。')
    st.header('設定')
    col1, col2, col3 = st.columns(3)
    with col1:
        initial_stack_for_tournament_input = st.number_input(
            '初期スタックサイズ (チップ点数)', min_value=100, value=st.session_state.initial_stack_for_tournament_set, step=100, key="initial_stack_input"
        )
    with col2:
        tournament_type_input = st.selectbox(
            'ブラインドスピード', ('ロング', 'ノーマル', 'ターボ', 'ハイパーターボ'),
            index=('ロング', 'ノーマル', 'ターボ', 'ハイパーターボ').index(st.session_state.tournament_type_set),
            key="tournament_type_select"
        )
    with col3:
        tournament_format_input = st.selectbox(
            'トーナメント形式', ('通常', 'ノックアウト (KO)', 'プログレッシブノックアウト (PKO)'),
            index=('通常', 'ノックアウト (KO)', 'プログレッシブノックアウト (PKO)').index(st.session_state.tournament_format_set),
            key="tournament_format_select"
        )
    game_mode_input = st.selectbox(
        'ゲームモード', ('ノーリミットホールデム', 'オマハ', 'スプリットホールデム'),
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
    if st.session_state.tournament_structure_df.empty: st.warning('まず「トーナメント ブラインドストラクチャー」ページでストラクチャーを確定してください。'); st.stop()
    df = st.session_state.tournament_structure_df
    current_level_idx = st.session_state.current_level_idx
    total_levels = len(df)
    if current_level_idx < total_levels:
        current_level_data = df.iloc[current_level_idx]
    else:
        st.info("全てのレベルが終了しました！お疲れ様でした！")
        st.session_state.timer_running = False
        current_level_data = {"レベル": "終了", "SB": "-", "BB": "-", "BBアンティ": "-", "レベル時間 (分)": 0}
    st.subheader("トーナメント概要")
    col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
    with col_summary1: st.markdown(f"**ゲームモード:** {st.session_state.game_mode_set}")
    with col_summary2: st.markdown(f"**初期スタック:** {st.session_state.initial_stack_for_tournament_set}点")
    with col_summary3: st.markdown(f"**ブラインドスピード:** {st.session_state.tournament_type_set}")
    with col_summary4:
        if st.session_state.tournament_format_set != '通常': st.markdown(f"**バウンティオプション:** {st.session_state.tournament_format_set}")
        else: st.markdown(f"**バウンティオプション:** なし")
    st.markdown("---")
    st.subheader("現在の参加状況")
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.session_state.entries = st.number_input('エントリー人数', min_value=1, value=st.session_state.entries, step=1, key='entries_input')
    with col_info2:
        st.session_state.remaining_players = st.number_input(
            '残り人数', min_value=1, max_value=st.session_state.entries,
            value=min(st.session_state.remaining_players, st.session_state.entries), step=1, key='remaining_players_input'
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
    st.markdown("---")
    if current_level_idx + 1 < total_levels:
        next_level_data = df.iloc[current_level_idx + 1]
        st.markdown(f"""
        <div style="text-align: center; font-size: 24px; color: gray;">
            次のレベル: {next_level_data["レベル"]} (SB: {next_level_data["SB"]} / BB: {next_level_data["BB"]} / BBアンティ: {next_level_data["BBアンティ"]})
        </div>
        """, unsafe_allow_html=True)
    else: st.markdown(f"""
        <div style="text-align: center; font-size: 24px; color: gray;">
            次のレベルはありません (最終レベル)
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")
    time_display_placeholder = st.empty()
    col_controls1, col_controls2, col_controls3 = st.columns(3)
    with col_controls1:
        if st.button('◀️ 1分戻す'): st.session_state.remaining_time_seconds = max(0, st.session_state.remaining_time_seconds + 60); st.rerun()
        if st.button('◀️ 1レベル戻す'):
            if st.session_state.current_level_idx > 0:
                st.session_state.current_level_idx -= 1
                new_level_data = df.iloc[st.session_state.current_level_idx]
                st.session_state.remaining_time_seconds = new_level_data['レベル時間 (分)'] * 60
                st.session_state.timer_running = False
                st.rerun()
            else: st.warning("これ以上戻るレベルはありません。")
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
                st.session_state.timer_running = False
                st.rerun()
            else: st.warning("これ以上進むレベルはありません。")
    with col_controls3:
        if st.session_state.timer_running:
            if st.button('⏸️ タイマー停止'): st.session_state.timer_running = False; st.rerun()
        else:
            if st.button('▶️ タイマー開始'): st.session_state.timer_running = True; st.rerun()
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
    if current_level_idx < total_levels: st.dataframe(df.iloc[current_level_idx:].reset_index(drop=True), hide_index=True, use_container_width=True)
    else: st.write("全てのブラインドレベルが表示されました。")

# --- ピッケムページ ---
elif page_selection == "ピッケム":
    st.title('ピッケム')
    st.write('プレイしたいゲームモードを選択してください。')

    pickem_game_mode_options = [
        'Holdem - Normal', 'Holdem - Super',
        'Drawmaha - Hi', 'Drawmaha - 27 lowball', 'Drawmaha - A5 lowball', 'Drawmaha - Badugi', 'Drawmaha - Hi-dugi',
        'Drawmaha - 0', 'Drawmaha - 49',
        'Draw - Hi', 'Draw - 27 lowball', 'Draw - A5 lowball', 'Draw - Badugi', 'Draw - Hi-dugi', 'Draw - Badacey',
        'Draw - Badeucey', 'Draw - Archie',
        'Stud - Super Stud', 'Stud - Super Stud H/L8',
        'Omaha - Double Board Hi/Hi (4 or 5枚)', 'Omaha - Double Board Best/Best (4 or 5枚)'
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
    
    st.markdown("---")
    st.subheader("ゲームのルール")
    selected_game = st.session_state.pickem_game_mode
    rules = game_rules.get(selected_game, "このゲームのルールはまだ登録されていません。")
    st.markdown(rules)