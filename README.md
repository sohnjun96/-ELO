# 테정테세문단세 ELO 랭킹 시스템

### 주소
![{CDEB9789-B112-46A2-902A-A2C2A881F03D}](https://github.com/user-attachments/assets/e5aebe71-0fb3-435e-91cf-2f36ccae5f9b)
https://tjtsmds.streamlit.app/

## ELO 시스템이란?
Elo(ELO) 레이팅 시스템은 경기 결과를 기반으로 플레이어 또는 팀의 상대적 실력을 평가하는 통계적 방법이다. 1950년대에 체스 마스터 아르파드 엘로(Arpad Elo)에 의해 개발되었으며, 현재 체스, 스포츠 리그, e스포츠, 보드 게임 등 다양한 분야에서 사용된다.
- 실력 차가 많이 나는 상대를 이기면 점수가 많이 오르는 시스템
- 복식은 팀별 평균 점수로 계산
- 대회 시작 직전 ELO 기준으로 계산해서 대회 끝난 뒤 한꺼번에 반영
- 초기 ELO는 2,000점, 대회 규모별 차등 계수(K) 적용(정기: 200, 상시: 100, 친선: 0)
  - 기준: 정기(6인 이상), 상시(4인 이상)
  - 경기별로 보너스 점수(정기: 4, 상시: 1, 친선: 0)


## 시스템 설명

### 1. 선수등록
- "홈" 화면에서 선수 등록 후 대회진행 가능
- 초기 ELO는 2,000점으로 설정됨

### 2. 대회진행
- 왼쪽 위의 ">" 모양을 눌러서 "대회진행" 탭으로 이동
- 진행 중인 대회가 표시되거나, 새로운 대회 시작 가능
- "대회진행" 탭에서 대회명, 대회일자, 대회종류와 참가자를 입력
- [경기 기록] 버튼으로 경기(단식/복식)를 기록할 수 있음
  - **설정** - 대회 정보를 수정할 수 있음. 대회종류는 경기 입력 전까지만 수정 가능
  - **분석** - 참가자들의 ELO 랭킹과 ELO 계산식에 따른 승률 분석을 제공
  - **현황** - 기록된 경기를 표시함 / [경기 삭제] 버튼으로 입력된 경기를 삭제 가능
  - **종료** - [대회 종료] 대회를 종료하고 데이터를 서버에 전송 / [대회 취소] 대회를 취소함
    - ELO 점수는 한 대회에서 경기의 순서와 상관없이 경기 전 ELO를 기준으로 계산해서 일괄 반영

### 3. 각종 통계
- "대회기록", "선수별 기록" 탭에서 경기 결과 및 통계를 확인 가능

### 4. 백업기능
- 이 시스템은 streamlit community cloud(SCC) 시스템에서 이 Github repository를 복사한 후 구동되는 방식임.
- 따라서 한동안 접속이 없으면 SCC 세선이 만료되고 재부팅시 다시 이 Github repository를 clone 하므로, 데이터를 다른 곳에 저장하고 불러오는 구조가 필요함. 
- Slack 채널에 대회가 끝날때마다 자동으로 업로드하고, 재부팅시마다 Slack 채널에서 최신버전 여부를 확인하여 새고고침할 수 있도록 구성됨.


## 개발

### ToDo
- [ ] 디자인 개선
- [ ] 개인별 ELO 트래킹 기능 개선
- [ ] 선수 삭제 기능
- [x] 초기화 기능 추가
- [ ] 점수 조정 기능 추가
- [ ] Slack 서버에서 파일을 내려받는 기능 & 현재 파일이 최신(대회 기준)이 아닐 시 내려받는 기능 추가

### Issue
- [x] 대회 진행 중에 현황(승무패) 잘못출력되는중
- [x] 재부팅시 선수 날아가는 문제 -> data.xlsx가 제대로 수정되지 않는듯
- [ ] [선수별 기록] 최근 참가 대회가 옛날꺼부터 표시됨

### 토의
- [x] 대회별/경기별 추가 점수 지급량 개선

패치노트
#### 250126
- 자동 패치기능 추가
#### 250208
- 델타가 개인별로 계산되도록 수정
