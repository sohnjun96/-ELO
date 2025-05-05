from ELO import *
import pandas as pd
import streamlit as st
import pickle
import os
from datetime import datetime
from 홈 import create_recent_games_form
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 파일 경로 설정
data_file_path = "data/data.xlsx"
state_file_path = "data/state.pickle"

# 데이터 초기화
elo_hist, games_hist = load_excel(data_file_path)
ranking_table = create_ranking_table(elo_hist)
등록선수 = ranking_table["이름"].unique()

def ZeroDivision(num1, num2):
    if num2 >= 3:
        result = round(num1/num2*100)
    else:
        result = 0
    return result

# 색상 테마 설정
COLOR_WIN = '#2196F3'  # 승리 색상 (파란색)
COLOR_LOSE = '#F44336'  # 패배 색상 (빨간색)
COLOR_PRIMARY = '#1E88E5'  # 주요 차트 색상 (파란색)

# 통계 데이터 생성
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
st.header("🎯 전체 통계")

# 상단 요약 카드
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("총 선수 수", len(등록선수))
with col2:
    st.metric("총 경기 수", len(games_hist))
with col3:
    st.metric("총 대회 수", len(games_hist['대회명'].unique()))
with col4:
    st.metric("평균 ELO", round(통계_전체['ELO 현재'].mean()))

# 모든 선수의 ELO 점수 추적
elo_trend = pd.DataFrame()
for player in 등록선수:
    player_elo = 검색_ELO(elo_hist, player)
    player_elo['선수'] = player
    elo_trend = pd.concat([elo_trend, player_elo])

tab1, tab2, tab3 = st.tabs(["랭킹", "경기", "대회"])

with tab1:
    st.subheader("랭킹 및 ELO 통계")
    
    # ELO 분포 히스토그램
    fig = go.Figure()
    
    # 히스토그램 데이터 계산 (bin 수를 줄여서 더 간략하게)
    hist_data = 통계_전체['ELO 현재']
    hist, bin_edges = np.histogram(hist_data, bins=10)  # bin 수를 20에서 10으로 줄임
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # 부드러운 곡선 추가 (smoothing 값을 높여서 더 부드럽게)
    fig.add_trace(go.Scatter(
        x=bin_centers,
        y=hist,
        mode='lines',
        line=dict(
            shape='spline',
            smoothing=0.6,  # smoothing 값을 0.3에서 0.6으로 증가
            color=COLOR_PRIMARY,
            width=3
        ),
        fill='tozeroy',
        fillcolor='rgba(30, 136, 229, 0.2)',
        name='ELO 분포'
    ))
    
    # 평균 ELO 점수 선 추가
    평균_ELO = 통계_전체['ELO 현재'].mean()
    표준편차 = 통계_전체['ELO 현재'].std()
    
    fig.add_vline(
        x=평균_ELO,
        line_dash="dash",
        line_color="red",
        annotation_text=f"평균: {int(평균_ELO)}",
        annotation_position="top right"
    )
    
    # 표준편차 범위 표시
    fig.add_vrect(
        x0=평균_ELO - 표준편차,
        x1=평균_ELO + 표준편차,
        fillcolor="gray",
        opacity=0.2,
        line_width=0,
        annotation_text=f"±{int(표준편차)}",
        annotation_position="top left"
    )
    
    # 레이아웃 설정 (그래프를 더 간단하게)
    fig.update_layout(
        title='ELO 점수 분포',
        xaxis_title='ELO 점수',
        yaxis_title='선수 수',
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',  # 플롯 배경을 투명하게
        paper_bgcolor='rgba(0,0,0,0)',  # 전체 배경을 투명하게
        xaxis=dict(
            gridcolor='lightgray',
            zerolinecolor='lightgray',
            showgrid=False
        ),
        yaxis=dict(
            gridcolor='lightgray',
            zerolinecolor='lightgray',
            showgrid=False
        ),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ELO 통계 요약
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("평균 ELO", int(평균_ELO))
    with col2:
        st.metric("표준편차", int(표준편차))
    with col3:
        st.metric("최고 ELO", int(통계_전체['ELO 최고'].max()))
    
    # 랭킹 및 ELO 테이블
    st.dataframe(통계_전체[["랭킹_현재", "ELO 현재", "ELO 최고", "ELO 최저"]]
                .sort_values('랭킹_현재', ascending=True)
                .style.background_gradient(subset=['ELO 현재'], cmap='Blues'),
                use_container_width=True)
    
    # 선수 선택을 위한 드롭다운 (랭킹 탭)
    st.subheader("선수별 ELO 추이 분석")
    selected_players_ranking = st.multiselect(
        "분석하고 싶은 선수를 선택하세요",
        options=등록선수,
        default=등록선수.tolist(),
        key="ranking_players"
    )
    
    # 선택된 선수들의 ELO 추이 그래프
    if selected_players_ranking:
        fig = px.line(elo_trend[elo_trend['선수'].isin(selected_players_ranking)], 
                      x='날짜', 
                      y='ELO', 
                      color='선수',
                      title='선택한 선수들의 ELO 점수 추이',
                      markers=True)
        fig.update_layout(
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("경기 통계")
    
    종류_select = st.pills("종류", ["승률", "승리 수", "경기 수"], default="승률")
    단복_select = st.segmented_control("단식복식", ["전체", "단식", "복식"], default="전체")
    
    # 데이터프레임 준비
    df1 = 통계_전체[["전체_승률", "전체_경기수", "전체_승리수", "전체_패배수"]].rename(
        columns={"전체_승률":"승률", "전체_경기수":"경기", "전체_승리수":"승리", "전체_패배수":"패배"})
    df2 = 통계_전체[["단식_승률", "단식_경기수", "단식_승리수", "단식_패배수"]].rename(
        columns={"단식_승률":"승률", "단식_경기수":"경기", "단식_승리수":"승리", "단식_패배수":"패배"})
    df3 = 통계_전체[["복식_승률", "복식_경기수", "복식_승리수", "복식_패배수"]].rename(
        columns={"복식_승률":"승률", "복식_경기수":"경기", "복식_승리수":"승리", "복식_패배수":"패배"})
    
    # 선택에 따른 데이터프레임 선택
    if 단복_select == "전체":
        df = df1
    elif 단복_select == "단식":
        df = df2
    else:
        df = df3
    
    # 정렬 기준 선택
    if 종류_select == "승률":
        df = df.sort_values('승률', ascending=False)
    elif 종류_select == "승리 수":
        df = df.sort_values('승리', ascending=False)
    else:
        df = df.sort_values('경기', ascending=False)
    
    # 차트 생성
    fig = go.Figure()
    
    if 종류_select == "승률":
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['승률'],
            name='승률',
            marker_color=COLOR_PRIMARY,
            text=df['승률'].apply(lambda x: f"{x}%"),
            textposition='auto'
        ))
        fig.update_layout(
            title=f'{단복_select} 승률 TOP 10',
            yaxis_title='승률 (%)',
            height=400
        )
    elif 종류_select == "승리 수":
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['승리'],
            name='승리',
            marker_color=COLOR_WIN,
            text=df['승리'],
            textposition='auto'
        ))
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['패배'],
            name='패배',
            marker_color=COLOR_LOSE,
            text=df['패배'],
            textposition='auto'
        ))
        fig.update_layout(
            title=f'{단복_select} 승패 수 TOP 10',
            yaxis_title='경기 수',
            barmode='stack',
            height=400
        )
    else:
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['경기'],
            name='경기 수',
            marker_color=COLOR_PRIMARY,
            text=df['경기'],
            textposition='auto'
        ))
        fig.update_layout(
            title=f'{단복_select} 경기 수 TOP 10',
            yaxis_title='경기 수',
            height=400
        )
    
    # 텍스트 스타일 설정
    fig.update_traces(
        textfont_size=12,
        textangle=0,
        textposition="auto",
        cliponaxis=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 데이터프레임 표시
    config = {
        "승률": st.column_config.NumberColumn(format="%d %%"),
        "경기": st.column_config.NumberColumn(format="%d 경기"),
        "승리": st.column_config.NumberColumn(format="%d 승"),
        "패배": st.column_config.NumberColumn(format="%d 패")
    }
    st.dataframe(df.head(10), column_config=config)

with tab3:
    st.subheader("대회 통계")
    
    # 대회별 경기 수
    대회별_경기수 = games_hist.groupby('대회명').size().reset_index(name='경기수')
    대회별_경기수 = 대회별_경기수.sort_values('경기수', ascending=False)
    
    fig = px.bar(대회별_경기수.head(10), 
                 x='대회명', 
                 y='경기수',
                 title='대회별 경기 수 TOP 10',
                 color_discrete_sequence=[COLOR_PRIMARY])
    st.plotly_chart(fig, use_container_width=True)
    
    # 최근 대회 결과
    st.subheader("최근 대회 결과")
    최근_대회 = games_hist.sort_values('날짜', ascending=False).head(20)
    st.dataframe(최근_대회[['날짜', '대회명', '이름1', '이름2', '점수1', '점수2', '복식여부']],
                use_container_width=True)
