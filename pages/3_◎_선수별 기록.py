from ELO import *
import pandas as pd
import streamlit as st
import pickle
import os
from datetime import datetime
from 홈 import create_recent_games_form

# 파일 경로 설정
data_file_path = "data/data.xlsx"
state_file_path = "data/state.pickle"

# 엑셀 로드 함수
def load_excel(file_path):
    data = pd.ExcelFile(file_path)
    elo_hist = data.parse("ELO")
    games_hist = data.parse("Games")
    return elo_hist, games_hist
    
# 랭킹 테이블 생성 함수
def create_ranking_table(elo_hist):
    elo_hist['날짜'] = pd.to_datetime(elo_hist['날짜'], errors='coerce')
    elo_hist = elo_hist.dropna(subset=['날짜'])
    latest_elo = (
        elo_hist.groupby('이름').apply(lambda x: x.loc[x['날짜'].idxmax()])
        .reset_index(drop=True)
    )
    ranking_table = latest_elo.sort_values(['ELO', '날짜'], ascending=[False, False]).reset_index(drop=True)
    ranking_table = ranking_table[['이름', 'ELO']]
    ranking_table.index += 1  # 인덱스를 1부터 시작하도록 설정
    return ranking_table

# ELO 점수 확인
def elo_check(ranking_table, name):
    return ranking_table.loc[ranking_table['이름']==name,["ELO"]].iloc[0,0]

# 입력_이름의 ELO 검색
def 검색_ELO(elo_hist, 입력_이름):
    return elo_hist.loc[elo_hist["이름"] == 입력_이름]

# 입력_이름의 전적 검색
def 검색_게임(games_hist, 입력_이름):
    조건 = (games_hist["이름1"] == 입력_이름) + (games_hist["이름1A"] == 입력_이름) + (games_hist["이름2"] == 입력_이름) + (games_hist["이름2A"] == 입력_이름)
    df = games_hist.loc[조건]
    return process_matches(df.loc[조건], 입력_이름)

# 승자 및 팀 정보 반환 함수
def get_match_result(row, name):
    def format_names(row):
        if row['복식여부'] == '복식':
            player1 = f"{row['이름1']} & {row['이름1A']}" if row['이름1A'] else row['이름1']
            player2 = f"{row['이름2']} & {row['이름2A']}" if row['이름2A'] else row['이름2']
        else:
            player1 = row['이름1']
            player2 = row['이름2']
        return player1, player2
    
    player1, player2 = format_names(row)
    
    # 이름1, 이름1A에 해당하는 팀 점수
    if name in [row['이름1'], row['이름1A']]:
        my_score = row['점수1']
        opponent_score = row['점수2']
        my_team = player1
        opponent_team = player2
    # 이름2, 이름2A에 해당하는 팀 점수
    elif name in [row['이름2'], row['이름2A']]:
        my_score = row['점수2']
        opponent_score = row['점수1']
        my_team = player2
        opponent_team = player1
    else:
        return "이름이 입력되지 않았습니다."
    
    # 승자 판별
    if my_score > opponent_score:
        winner = '승리'
    elif my_score < opponent_score:
        winner = '패배'
    else:
        winner = '무승부'
    
    # 반환할 결과
    result = {
        '이름': name,
        '팀1': my_team,
        '점수1': my_score,
        '팀2': opponent_team,
        '점수2': opponent_score,
        '날짜': row['날짜'],
        '대회명': row['대회명'],
        'K값': row['K값'],
        '복식여부': row['복식여부'],
        '델타': row['델타']
    }
    return result

# 각 행에 대해 결과 생성
def process_matches(df, name):
    results = []
    for _, row in df.iterrows():
        result = get_match_result(row, name)
        results.append(result)
    return pd.DataFrame(results)[["날짜", "대회명", "팀1", "팀2","점수1",  "점수2", "K값", "복식여부", "델타"]].fillna('').sort_values("날짜", ascending=False)

# 데이터 초기화
elo_hist, games_hist = load_excel(data_file_path)
ranking_table = create_ranking_table(elo_hist)
등록선수 = ranking_table["이름"].unique()

# 선수 선택
입력_이름 = st.selectbox("선수를 선택해주세요. ",등록선수)

try:
    # 선수 정보 검색
    검색결과 = 검색_게임(games_hist, 입력_이름)
    게임_전적 = 전적계산(검색결과)
    ELO_전적 = 검색_ELO(elo_hist, 입력_이름)
    
    ELO_현재 = round(elo_check(ranking_table, 입력_이름))
    랭킹_현재 = ranking_table.index[(ranking_table["이름"]==입력_이름)][0]

    st.title(입력_이름)
    st.write(f'#### **전적**: 총 {게임_전적["전체"]} 게임 ({게임_전적["승리"]} 승 / {게임_전적["무승부"]} 무 / {게임_전적["패배"]} 패)')
    st.write(f'#### **ELO**: {ELO_현재} 점 ({랭킹_현재} 위)')
    st.write(f'#### **최근 참가 대회**: {검색결과["대회명"][0]}({검색결과["날짜"][0]})')
    
    tabs = st.tabs(["전적", "ELO변동", "분석"])
    
    
    with tabs[0]:
        st.header("경기 결과")
        with st.container(border=True, height = 800):
            for idx, game in 검색결과.iterrows():
                create_recent_games_form(game)
    with tabs[1]:
        st.write(ELO_전적)
    with tabs[2]:
        st.warning("제작 중...")
    
except Exception as e:
    st.error(f"선수 데이터를 로드하는 중 오류 발생: 경기 기록 없음")
    