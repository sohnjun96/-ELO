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


def num_of_matchs(matches):
    try:
        return len(matches) - len(matches.loc[matches["대회명"] == "등록"])
    except:
        return 0

def num_of_games(games):
    try:
        return len(games)
    except:
        return 0    

# 데이터 초기화
elo_hist, games_hist = load_excel(data_file_path)
ranking_table = create_ranking_table(elo_hist)
등록선수 = ranking_table["이름"].unique()

# 선수 선택
입력_이름 = st.selectbox("선수를 선택해주세요. ",등록선수)

try:
    대회수 = num_of_matchs(검색_ELO(elo_hist, 입력_이름))
    경기수 = num_of_games(검색_게임(games_hist, 입력_이름))
    
    # 선수 정보 검색
    검색결과 = 검색_게임(games_hist, 입력_이름)
    게임_전적 = 전적계산(검색결과)
    ELO_전적 = 검색_ELO(elo_hist, 입력_이름)
    
    ELO_현재 = round(elo_check(ranking_table, 입력_이름))
    랭킹_현재 = ranking_table.index[(ranking_table["이름"]==입력_이름)][0]

    st.write(f'### {입력_이름}')
    st.write(f'**대회**: 총 {대회수} 회')
    st.write(f'**전적**: 총 {게임_전적["전체"]} 경기 ({게임_전적["승리"]} 승 / {게임_전적["무승부"]} 무 / {게임_전적["패배"]} 패)')
    st.write(f'**ELO**: {ELO_현재} 점 ({랭킹_현재} 위)')
    st.write(f'**최근 참가 대회**: {검색결과["대회명"][len(검색결과)-1]} ({검색결과["날짜"][len(검색결과)-1]})')
    
    tabs = st.tabs(["전적", "ELO변동", "분석"])
    
    with tabs[0]:
        st.header("경기 결과")
        with st.container(border=True, height = 800):
            for idx, game in 검색결과.iloc[::-1].iterrows():
                create_recent_games_form(game)
    with tabs[1]:
        st.write(ELO_전적)
    with tabs[2]:
        st.warning("제작 중...")
    
except Exception as e:
    st.error(f"선수 데이터를 로드하는 중 오류 발생: 경기 기록 없음")
    
