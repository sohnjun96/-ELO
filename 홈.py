from ELO import *
import os
import numpy as np
import datetime as dt
import pandas as pd
import streamlit as st
from datetime import datetime
from slack import *
import shutil
import zipfile
import requests

# 파일 경로 설정
data_init_path = "data.xlsx"
data_file_path = "data/data.xlsx"
directory_path = 'data/pickles'

# 초기화
def DeleteAllFiles(filePath):
    if os.path.exists(filePath):
        for file in os.scandir(filePath):
            if file.path != "data/pickles/.gitkeep":
                os.remove(file.path)
        return True
    else:
        return False
    
def initialize(data_init_path, data_file_path, directory_path):
    with open('.version', 'w') as file:
        file.write(" ")
    if os.path.exists(data_file_path):
        os.remove(data_file_path)
    if os.path.exists(data_init_path):
        shutil.copy(data_init_path, data_file_path)
    DeleteAllFiles(directory_path)

    
# 최신 파일 압축 해제 및 적용
@st.cache_data
def 업데이트():
    # try:
    title = file_read()

    with open('.version', 'r') as file:
        title_0 = file.read()

    if title != title_0:
        with open('.version', 'w') as file:
            file.write(title)
        print(title)
        print(title_0)
        delete_data_folder()
        extract_zip_file('tmp.zip')
    # except:
    #     pass
    return title
    
# ELO 랭킹 폼 생성
def create_ELO_form(game):
    입력_이름 = game["이름"]
    try:
        대회수 = num_of_matchs(검색_ELO(st.session_state.elo_hist, 입력_이름))
        경기수 = num_of_games(검색_게임(st.session_state.games_hist, 입력_이름))
        # st.write(검색_게임(st.session_state.games_hist, 입력_이름))
        st.write(f'###### **{rank_emoji(idx)} {입력_이름}** -- {format(int(game["ELO"]),",")} 점 ({경기수} 경기 /{대회수} 대회)')
    except:
        st.write("")
        
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

# 최근 경기 폼 생성
def create_recent_games_form(game):
    with st.container(border=True):
        if game["복식여부"] == "복식":
            이모티콘 = " :couple: "
        else:
            이모티콘 = " "
        st.write(f'#### {game["날짜"]} {game["대회명"]} {이모티콘}')
        if game["점수1"] > game["점수2"]:
            델타1 = game["델타"]
            델타2 = (-1) * game["델타"]
            승패1 = ":crown: 승리"
            승패2 = ":skull: 패배"
        else:
            델타1 = (-1) * game["델타"]
            델타2 = game["델타"]
            승패1 = ":skull: 패배"
            승패2 = ":crown: 승리"
            
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label = f'{game["팀1"]}', value = f'{game["점수1"]}', delta = f'{round(델타1)} 점 ELO')
            st.write(승패1)
        with col2:
            st.metric(label = f'{game["팀2"]}', value = f'{game["점수2"]}', delta = f'{round(델타2)} 점 ELO')
            st.write(승패2)



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
    return pd.DataFrame(results)[["날짜", "대회명", "팀1", "팀2","점수1",  "점수2", "K값", "복식여부", "델타"]].fillna('')
    
# 입력_이름의 ELO 검색
def 검색_ELO(elo_hist, 입력_이름):
    return elo_hist.loc[elo_hist["이름"] == 입력_이름]

# 입력_이름의 전적 검색
def 검색_게임(games_hist, 입력_이름):
    try:
        조건 = (games_hist["이름1"] == 입력_이름) + (games_hist["이름1A"] == 입력_이름) + (games_hist["이름2"] == 입력_이름) + (games_hist["이름2A"] == 입력_이름)
        df = games_hist.loc[조건]
        result = process_matches(df.loc[조건], 입력_이름)
    except:
        result = None
    return result
    
# 새로운 선수 등록 함수
def add_new_player(elo_hist, player_name):
    today = datetime.today().strftime("%Y-%m-%d")
    new_player = {"날짜": today, "대회명": "등록", "K값": 0, "이름": player_name, "ELO": 2000}
    elo_hist = pd.concat([elo_hist, pd.DataFrame([new_player])], ignore_index=True)
    return elo_hist

# 압축 해제 함수
def extract_zip_file(uploaded_file):
    """주어진 zip 파일을 현재 디렉토리에 압축 해제하는 함수"""
    # 현재 디렉토리로 압축 해제
    current_dir = os.getcwd()

    # 업로드된 파일을 zip 파일로 처리
    with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
        # 압축 해제
        zip_ref.extractall(current_dir)
        # st.success(f"{uploaded_file.name} 파일의 압축을 현재 디렉토리에 성공적으로 풀었습니다.")

    # 압축 해제된 파일 목록 표시
    extracted_files = os.listdir(current_dir)
    # st.write("압축 해제된 파일 목록:")
    # st.write(extracted_files)

# 'data' 폴더 삭제 함수
def delete_data_folder(folder="data"):
    """data 폴더와 그 안의 모든 파일을 삭제하는 함수"""
    if os.path.exists(folder):
        shutil.rmtree(folder)
        st.success(f"{folder} 폴더와 그 안의 모든 파일을 삭제했습니다.")
    else:
        st.warning(f"{folder} 폴더가 존재하지 않습니다.")

# 파일 경로
file_path = "data/data.xlsx"


# Streamlit 페이지 작성
st.title(":tennis: 	테정테세문단세")
    
# 세션 상태 초기화
if "elo_hist" not in st.session_state or "games_hist" not in st.session_state:
    업데이트()
    
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
            
def ELO_시뮬레이션_form(elo_system):
    with st.popover("ELO 승패 시뮬레이션"):
        st.write("### ELO 승패 시뮬레이션")
        col1, col2 = st.columns(2)
        with col1:
            ELO1 = st.number_input("선수1의 ELO: ", value = 2000, min_value = 1, max_value = 4000)
            점수1 = st.number_input("선수1의 득점: ", value = 6, min_value = 0, max_value = 10)
        with col2:
            ELO2 = st.number_input("선수2의 ELO: ", value = 2000, min_value = 1, max_value = 4000)
            점수2 = st.number_input("선수2의 득점: ", value = 0, min_value = 0, max_value = 10)

        elo_system.초기화()
        if (ELO1!=0) and (ELO2!=0):
            tournament_type = st.radio(
                "대회종류",
                ["정기", "상시", "친선"],
                help=f"정기는 K={k_정기}, 상시는 K={k_상시}, 친선은 K={k_친선} 입니다",
            )
                # ELO에 k 값 수정
            if tournament_type == "정기":
                elo_system.k = k_정기
            elif tournament_type == "상시":
                elo_system.k = k_상시
            else:
                elo_system.k = k_친선

            elo_system.등록("선수1", ELO1)
            elo_system.등록("선수2", ELO2)
            elo_system.게임("선수1","선수2",scoring(점수1, 점수2))
            result = elo_system.종료()
            델타1 = result["선수1"] - ELO1
            델타2 = result["선수2"] - ELO2
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label = f'{"선수1"}', value = f'{result["선수1"]}', delta = f'{round(델타1)} 점 ELO')
            with col2:
                st.metric(label = f'{"선수2"}', value = f'{result["선수2"]}', delta = f'{round(델타2)} 점 ELO')
        else:
            st.write("선수들의 득점을 확인해주세요.")
            
           
# 랭킹 섹션
st.write("### :trophy: ELO 랭킹")
ranking_table = create_ranking_table(st.session_state.elo_hist)

with st.container(border=True, height = 400):
    # ELO 랭킹 폼 생성
    for idx, game in ranking_table.iterrows():
        with st.container(border=True):
            create_ELO_form(game)

# with st.container(border=True):
col1, col2, col3 = st.columns(3)
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

if "register" not in st.session_state:
    with col3:
        if st.button("선수 등록"):
            register_player()
else:
    st.write(f"선수 '{st.session_state['register']}'이 등록되었습니다.")

with col2:
    elo_system = Elo()
    ELO_시뮬레이션_form(elo_system)

st.divider()
            
# 최근 경기 섹션
st.write("### :chart: 최근 경기 ")
try:
    recent_games_table = create_recent_games_table(st.session_state.games_hist)
    # st.dataframe(recent_games_table)

    with st.container(border=True, height = 500):
        for idx, game in recent_games_table.iterrows():
            create_recent_games_form(game)
            
except Exception as e:
    st.error("저장된 경기가 없습니다. ")

with st.popover("테정테세"):
    st.image("logo.webp")
    st.caption("제작자: 손준혁 using ChatGPT")
    init = st.text_input(" ")
    if init == "관리자":
        btn = st.button("초기화")
        if btn:
            initialize(data_init_path, data_file_path, directory_path)
            st.rerun()
        btn = st.button("다운로드")
        if btn:
            file_path = 'data'

            zip_file = zipfile.ZipFile("data.zip", "w")  # "w": write 모드
            for (path, dir, files) in os.walk(file_path):
                for file in files:
                    zip_file.write(os.path.join(path, file), compress_type=zipfile.ZIP_DEFLATED)

            zip_file.close()
            
            with open("data.zip", "rb") as file:
                btn = st.download_button(
                    label="다운로드",
                    data=file,
                    file_name=f'data_{datetime.today()}.zip',
                )
            
        if st.button("SLACK 전송"):
            file_path = 'data'

            zip_file = zipfile.ZipFile("data.zip", "w")  # "w": write 모드
            for (path, dir, files) in os.walk(file_path):
                for file in files:
                    zip_file.write(os.path.join(path, file), compress_type=zipfile.ZIP_DEFLATED)

            zip_file.close()
            
            slack_upload("data.zip", f'data_{datetime.now().date()}')
            st.write("완료")
        
        uploaded_file = st.file_uploader("ZIP 파일을 선택하세요", type=["zip"])
        if uploaded_file is not None:
            # 압축 해제 함수 호출
            delete_data_folder()
            extract_zip_file(uploaded_file)
            st.rerun()
            
        if st.button("업데이트"):
            # 압축 해제 함수 호출
            업데이트()
            # st.rerun()
            