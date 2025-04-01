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
st.header(":file_folder: 전체 통계")

tab1, tab2, tab3 = st.tabs(["랭킹", "경기", "대회"])

with tab1:
    
    st.write(통계_전체[["랭킹_현재", "ELO 현재","ELO 최고", "ELO 최저"]].sort_values('랭킹_현재', ascending=True))


with tab2:
    종류_select = st.pills("종류", ["승률", "승리 수", "경기 수"], default="승률")
    단복_select = st.segmented_control("단식복식", ["전체", "단식", "복식"], default="전체")
    
    df1 = 통계_전체[["전체_승률", "전체_경기수","전체_승리수", "전체_패배수"]].rename(columns={"전체_승률":"승률","전체_경기수":"경기", "전체_승리수":"승리", "전체_패배수":"패배"})
    df2 = 통계_전체[["단식_승률", "단식_경기수","단식_승리수", "단식_패배수"]].rename(columns={"단식_승률":"승률","단식_경기수":"경기", "단식_승리수":"승리", "단식_패배수":"패배"})
    df3 = 통계_전체[["복식_승률", "복식_경기수","복식_승리수", "복식_패배수"]].rename(columns={"복식_승률":"승률","복식_경기수":"경기", "복식_승리수":"승리", "복식_패배수":"패배"})
    config = {"승률":st.column_config.NumberColumn(
            format="%d %%",
        )}
    if 종류_select == "승률":

        if 단복_select == "전체":
            st.dataframe(df1.sort_values('승률', ascending=False), column_config=config)
        elif 단복_select == "단식":
            st.dataframe(df2.sort_values('승률', ascending=False), column_config=config)
        elif 단복_select == "복식":
            st.dataframe(df3.sort_values('승률', ascending=False), column_config=config)

    elif 종류_select == "승리 수":
        if 단복_select == "전체":
            st.dataframe(df1.sort_values('승리', ascending=False), column_config=config)
        elif 단복_select == "단식":
            st.dataframe(df2.sort_values('승리', ascending=False), column_config=config)
        elif 단복_select == "복식":
            st.dataframe(df3.sort_values('승리', ascending=False), column_config=config)

    else:
        if 단복_select == "전체":
            st.dataframe(df1.sort_values('경기', ascending=False), column_config=config)
        elif 단복_select == "단식":
            st.dataframe(df2.sort_values('경기', ascending=False), column_config=config)
        elif 단복_select == "복식":
            st.dataframe(df3.sort_values('경기', ascending=False), column_config=config)
    
    
with tab3:
    경기결과 = games_hist.sort_values('날짜', ascending=False)
    경기결과.set_index("대회명", inplace=True)
    st.write(경기결과)
