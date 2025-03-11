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


# 데이터 초기화
elo_hist, games_hist = load_excel(data_file_path)
ranking_table = create_ranking_table(elo_hist)
등록선수 = ranking_table["이름"].unique()

def ZeroDivision(num1, num2):
    
    if num2>=3:
        result = round(num1/num2*100)
    else:
        result = 0
        
    return result

통계_tmp = []

for 선수 in 등록선수:
    대회수 = num_of_matchs(검색_ELO(elo_hist, 선수))
    경기수 = num_of_games(검색_게임(games_hist, 선수))

    # 선수 정보 검색
    검색결과 = 검색_게임(games_hist, 선수)
    게임_전적 = 전적계산(검색결과)
    단식_전적 = 전적계산(검색결과[검색결과['복식여부']=='단식'])
    복식_전적 = 전적계산(검색결과[검색결과['복식여부']=='복식'])
    ELO_전적 = 검색_ELO(elo_hist, 선수)

    검색결과.index = 검색결과.index+1
    ELO_현재 = round(elo_check(ranking_table, 선수))
    랭킹_현재 = ranking_table.index[(ranking_table["이름"]==선수)][0]
    
    record = {
        "이름" : 선수,
        "랭킹_현재": 랭킹_현재,
        "ELO 현재" : ELO_현재,
        "ELO 최고" : ELO_전적["ELO"].max(),
        "ELO 최저" : ELO_전적["ELO"].min(),
        "대회수" : 대회수,
        "전체_경기수" : 게임_전적['전체'],
        "전체_승리수" : 게임_전적['승리'],
        "전체_패배수" : 게임_전적['패배'],
        "전체_승률" : ZeroDivision(게임_전적['승리'], 게임_전적['전체']),
        "단식_경기수" : 단식_전적['전체'],
        "단식_승리수" : 단식_전적['승리'],
        "단식_패배수" : 단식_전적['패배'],
        "단식_승률" : ZeroDivision(단식_전적['승리'], 단식_전적['전체']),
        "복식_경기수" : 복식_전적['전체'],
        "복식_승리수" : 복식_전적['승리'],
        "복식_패배수" : 복식_전적['패배'],
        "복식_승률" : ZeroDivision(복식_전적['승리'], 복식_전적['전체']),
    }
    통계_tmp.append(record)

통계_전체 = pd.DataFrame(통계_tmp)
통계_전체.set_index("이름", inplace=True)

# 여기서부터 표시코드
st.header(":file_folder:전체 통계")

# with st.container(border=True):
seg_select = st.segmented_control("", ["승률", "승리 수", "최고 경기"], default="승률")

if seg_select == "승률":
    st.write(통계_전체[["전체_승률", "전체_경기수","전체_승리수", "전체_패배수"]].sort_values('전체_승률', ascending=False))
elif seg_select == "승리 수":
    st.write(통계_전체[["전체_승률", "전체_경기수","전체_승리수", "전체_패배수"]].sort_values('전체_승리수', ascending=False))
else:
    st.write(통계_전체)
    
    