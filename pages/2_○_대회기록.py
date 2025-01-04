from ELO import *
import pandas as pd
import streamlit as st
import pickle
import os
from datetime import datetime

# 디렉토리 경로 지정
directory_path = 'data/pickles'

# 디렉토리에 있는 파일 목록 읽기
file_names = os.listdir(directory_path)
game_names = []
for file in file_names:
    game_names.append(file.split('.')[0])

state_file_path = directory_path + '/'+st.selectbox("대회를 선택해주세요.", game_names)+'.pickle'
    
# State 로드
def load_state():
    if os.path.exists(state_file_path):
        with open(state_file_path, "rb") as f:
            return pickle.load(f)
    return None

# ELO 점수 확인
def elo_check(ranking_table, name):
    return ranking_table.loc[ranking_table['이름']==name,["ELO"]].iloc[0,0]

# 승리 계수 계산
def scoring(score1, score2):
    return score1/(score1+score2)


# 데이터 로드
state = load_state()
elo_system = state["ELO"]["elo_system"]
elo_prev = state["ELO"]["기존"]
elo_result = state["ELO"]["결과"]

st.title(state["대회명"])
st.write(f"**대회일자**: {state['대회일자']}")
st.write(f"**대회종류**: {state['대회종류']}")

# 탭 구성
tabs = st.tabs(["정보", "결과", "분석"])

# 정보 탭
with tabs[0]:
    for 참가자 in state["참가자"]:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader(참가자)
        with col2:
            결과 = round(elo_result[참가자],)
            델타 = round(elo_result[참가자] - elo_prev[참가자],)
            st.metric(label="ELO", value = f"{결과} 점", delta=f"{델타} 점")

# 결과 탭
with tabs[1]:
    경기기록 = pd.DataFrame(state["경기기록"])
    경기기록.index = 경기기록.index+1
    단식 = 경기기록[경기기록["복식여부"] == "단식"]
    복식 = 경기기록[경기기록["복식여부"] == "복식"]
    
    if len(경기기록)>0:
        st.subheader(f"**경기(단식/복식)**: 총 {len(경기기록)} 회 ({len(단식)}/{len(복식)})")
        st.dataframe(경기기록)

    else:
        st.warning("경기를 기록해주세요. ")
    

# 분석 탭
with tabs[2]:
    st.subheader("분석")
    try:            
        st.write("ELO 점수")
        col1, col2 = st.columns(2)
        with col1:
            st.write("기존")
            st.dataframe(elo_prev)
        with col2:
            st.write("결과")
            st.dataframe(elo_result)
        st.write("승률 분석")
        st.dataframe(elo_system.승률())

    except Exception as e:
        st.error(f"랭킹 테이블을 생성하는 중 오류 발생: {e}")


