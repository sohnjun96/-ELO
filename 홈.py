import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
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
    recent_games = recent_games.sort_values('날짜', ascending=False).head(10)

    def format_names(row):
        if row['복식여부'] == 'Y':
            player1 = f"{row['이름1']}, {row['이름1A']}" if row['이름1A'] else row['이름1']
            player2 = f"{row['이름2']}, {row['이름2A']}" if row['이름2A'] else row['이름2']
        else:
            player1 = row['이름1']
            player2 = row['이름2']
        return player1, player2

    recent_games[['Player1', 'Player2']] = recent_games.apply(
        lambda row: pd.Series(format_names(row)), axis=1
    )
    recent_games['날짜'] = pd.to_datetime(recent_games['날짜']).dt.date
    recent_games = recent_games[['날짜', '대회명', 'Player1', 'Player2', '점수1', '점수2']]
    recent_games.reset_index(drop=True, inplace=True)
    recent_games.index += 1  # 인덱스를 1부터 시작하도록 설정
    return recent_games

# 새로운 선수 등록 함수
def add_new_player(elo_hist, player_name):
    today = datetime.today().strftime("%Y-%m-%d")
    new_player = {"날짜": today, "대회명": "등록", "K값": 0, "이름": player_name, "ELO": 2000}
    elo_hist = pd.concat([elo_hist, pd.DataFrame([new_player])], ignore_index=True)
    return elo_hist

# 파일 경로
file_path = "data/data.xlsx"

# Streamlit 페이지 작성
st.title("ELO & Games Tracker")

# 세션 상태 초기화
if "elo_hist" not in st.session_state or "games_hist" not in st.session_state:
    elo_hist, games_hist = load_excel(file_path)
    st.session_state.elo_hist = elo_hist
    st.session_state.games_hist = games_hist


# 선수 등록 모달 대화 상자 구현
@st.dialog("새로운 선수 등록")
def register_player():
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
    if st.button("새로운 선수 추가"):
        register_player()
else:
    st.write(f"선수 '{st.session_state['register']}'이 등록되었습니다.")

# 랭킹 섹션
st.header("Ranking")
ranking_table = create_ranking_table(st.session_state.elo_hist)
st.dataframe(ranking_table)

# 최근 경기 섹션
st.header("Recent Games")
recent_games_table = create_recent_games_table(st.session_state.games_hist)
st.dataframe(recent_games_table)