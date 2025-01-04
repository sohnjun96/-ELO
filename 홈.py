import numpy as np
import datetime as dt
import pandas as pd
import streamlit as st
from datetime import datetime

# 엑셀 로드 함수
def load_excel(file_path):
    data = pd.ExcelFile(file_path)
    elo_hist = data.parse("ELO")
    games_hist = data.parse("Games")
    return elo_hist, games_hist

# 엑셀 저장 함수
def save_to_excel(file_path, elo_hist, games_hist):
    with pd.ExcelWriter(file_path) as writer:
        elo_hist.to_excel(writer, sheet_name="ELO", index=False)
        games_hist.to_excel(writer, sheet_name="Games", index=False)

# 랭킹 테이블 생성 함수 수정
def create_ranking_table(elo_hist):
    elo_hist['날짜'] = pd.to_datetime(elo_hist['날짜'], errors='coerce')
    elo_hist = elo_hist.dropna(subset=['날짜'])
    latest_elo = (
        elo_hist.groupby('이름').apply(lambda x: x.loc[x['날짜'].idxmax()])
        .reset_index(drop=True)
    )
    ranking_table = latest_elo.sort_values(['ELO', '날짜'], ascending=[False, False]).reset_index(drop=True)
    ranking_table = ranking_table[['이름', 'ELO']]
    ranking_table["ELO"] = round(ranking_table["ELO"],0)
    ranking_table.index += 1  # 인덱스를 1부터 시작하도록 설정
    return ranking_table

# 최근 경기 테이블 생성
def create_recent_games_table(games_hist):
    
    recent_games = games_hist.copy()
    recent_games['날짜'] = pd.to_datetime(recent_games['날짜']).dt.date
    recent_games = recent_games.sort_values('날짜', ascending=False).head(5)

    def format_names(row):
        if row['복식여부'] == '복식':
            player1 = f"{row['이름1']} & {row['이름1A']}" if row['이름1A'] else row['이름1']
            player2 = f"{row['이름2']} & {row['이름2A']}" if row['이름2A'] else row['이름2']
        else:
            player1 = row['이름1']
            player2 = row['이름2']
        return player1, player2
 
    recent_games[['팀1', '팀2']] = recent_games.apply(
        lambda row: pd.Series(format_names(row)), axis=1
    )
    recent_games['날짜'] = pd.to_datetime(recent_games['날짜']).dt.date
    recent_games = recent_games[['날짜', '대회명', '팀1', '팀2', '점수1', '점수2', "K값", "복식여부", "델타"]]
    recent_games.reset_index(drop=True, inplace=True)
    recent_games.index += 1  # 인덱스를 1부터 시작하도록 설정
    return recent_games

# 경기 폼 생성
def create_recent_games_form(game):
    with st.container(border=True):
        st.write(f'#### {game["날짜"]} {game["대회명"]}')
        if game["점수1"] > game["점수2"]:
            델타1 = game["델타"]
            델타2 = (-1) * game["델타"]
        else:
            델타1 = (-1) * game["델타"]
            델타2 = game["델타"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label = f'{game["팀1"]}', value = f'{game["점수1"]}', delta = f'{round(델타1)} 점 ELO')
        with col2:
            st.metric(label = f'{game["팀2"]}', value = f'{game["점수2"]}', delta = f'{round(델타2)} 점 ELO')

# 새로운 선수 등록 함수
def add_new_player(elo_hist, player_name):
    today = datetime.today().strftime("%Y-%m-%d")
    new_player = {"날짜": today, "대회명": "등록", "K값": 0, "이름": player_name, "ELO": 2000}
    elo_hist = pd.concat([elo_hist, pd.DataFrame([new_player])], ignore_index=True)
    return elo_hist

# 파일 경로
file_path = "data/data.xlsx"

# Streamlit 페이지 작성
st.title("테정테세문단세")
st.header("ELO 랭킹 시스템")

col1, col2 = st.columns(2)
with col1:
    with st.popover("ELO 시스템이란?"):
        st.subheader("1. 개요")
        st.text("Elo(ELO) 레이팅 시스템은 경기 결과를 기반으로 플레이어 또는 팀의 상대적 실력을 평가하는 통계적 방법이다. 1950년대에 체스 마스터 아르파드 엘로(Arpad Elo)에 의해 개발되었으며, 현재 체스, 스포츠 리그, e스포츠, 보드 게임 등 다양한 분야에서 사용된다.")
        st.write("- 실력 차가 많이 나는 상대를 이기면 점수가 많이 오르는 시스템")
        st.write("- 복식은 팀별 평균 점수로 계산")
        st.write("- 대회 시작 직전 ELO 기준으로 계산해서 대회 끝난 뒤 한꺼번에 반영")
        st.write("- **초기 ELO는 2,000점**, 대회 규모별 차등 K 적용(정기: 200, 상시: 100, 친선: 0")
        st.divider()
        st.subheader("2. 계산")
        st.write("##### 1. 예상 승률 계산:")
        st.latex(r" E_A =  \frac{1}{1+10^{\frac{R_B - R_A}{400}}} ")
        st.write("##### 2. 레이팅 변동량 (ΔR) 계산:")
        st.latex(r"\Delta R = K \cdot (S - E)")
        st.latex(r"S_1 = \frac{s_1}{s_1+s_2}")
        st.write("- S: 경기 결과 (s1, s2: 선수1, 선수2의 점수)")
        st.write("- E: 예상 승률")
        st.write("##### 3. 복식 경기 팀 평균 레이팅:")
        st.latex(r"\text{Team A Rating} = \frac{R_{A1} + R_{A2}}{2}")
        st.latex(r"\text{Team B Rating} = \frac{R_{B1} + R_{B2}}{2}")
        st.write("##### 4. 복식 경기 예상 승률:")
        st.latex(r"E_A = \frac{1}{1 + 10^{\frac{\text{Team B Rating} - \text{Team A Rating}}{400}}}")
        st.write("##### 5. 레이팅 업데이트:")
        st.latex(r"\Delta R′=R+ΔR")
        st.write("- R': 업데이트된 레이팅")
        st.write("- R: 기존 레이팅")
    
# 세션 상태 초기화
if "elo_hist" not in st.session_state or "games_hist" not in st.session_state:
    elo_hist, games_hist = load_excel(file_path)
    st.session_state.elo_hist = elo_hist
    st.session_state.games_hist = games_hist


# 선수 등록 모달 대화 상자 구현
@st.dialog("새로운 선수 등록")
def register_player():
    st.write("초기 점수: 2,000점")
    
    player_name = st.text_input("새로운 선수의 이름을 입력:")
    if st.button("등록"):
        if player_name.strip():  # 이름이 비어있지 않은 경우만 추가
            st.session_state.elo_hist = add_new_player(st.session_state.elo_hist, player_name.strip())
            save_to_excel(file_path, st.session_state.elo_hist, st.session_state.games_hist)
            st.success(f"'{player_name}' 선수가 성공적으로 등록되었습니다!")
            st.rerun()  # 새로고침 실행
        else:
            st.error("선수 이름을 입력해주세요.")

if "register" not in st.session_state:
    with col2:
        if st.button("선수 등록"):
            register_player()
else:
    st.write(f"선수 '{st.session_state['register']}'이 등록되었습니다.")

# 랭킹 섹션
st.header("랭킹")
ranking_table = create_ranking_table(st.session_state.elo_hist)
st.dataframe(ranking_table)

# 최근 경기 섹션
st.header("최근 경기")
recent_games_table = create_recent_games_table(st.session_state.games_hist)
# st.dataframe(recent_games_table)

with st.container(border=True, height = 500):
    for idx, game in recent_games_table.iterrows():
        create_recent_games_form(game)

with st.popover("테정테세"):
    st.image("logo.webp")
    st.caption("제작자: 손준혁 using ChatGPT")
    
