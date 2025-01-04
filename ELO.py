class Elo:
    def __init__(self, initial_k=100, default_rating=2000):
        self.ratings = {}
        self.k = initial_k
        self.default_rating = default_rating
        self.pending_deltas = []  # 대기 중인 델타 저장

    def 등록(self, name, init_point=None):
        if name not in self.ratings:
            self.ratings[name] = init_point if init_point is not None else self.default_rating
            return True
        return False

    def 선수(self):
        return list(self.ratings.keys())

    def 델타(self, player_a, player_b, result_a):
        if player_a not in self.ratings or player_b not in self.ratings:
            raise ValueError(f"플레이어가 등록되지 않았습니다: {player_a}, {player_b}")

        rating_a = self.ratings[player_a]
        rating_b = self.ratings[player_b]

        expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
        delta = abs(self.k * (result_a - expected_a))
        delta_a = self.k * (result_a - expected_a)
        delta_b = -delta_a

        return round(delta_a, 2), round(delta_b, 2)

    def 델타_복식(self, team_a, team_b, result_a):
        if any(player not in self.ratings for player in team_a) or any(player not in self.ratings for player in team_b):
            raise ValueError(f"플레이어가 등록되지 않았습니다: {team_a}, {team_b}")

        avg_rating_a = sum(self.ratings[player] for player in team_a) / len(team_a)
        avg_rating_b = sum(self.ratings[player] for player in team_b) / len(team_b)

        expected_a = 1 / (1 + 10 ** ((avg_rating_b - avg_rating_a) / 400))
        expected_b = 1 - expected_a

        delta_a = self.k * (result_a - expected_a)
        delta_b = self.k * ((1 - result_a) - expected_b)

        return round(delta_a, 2), round(delta_b, 2)

    def 게임_복식(self, team_a, team_b, result_a):
        if any(player not in self.ratings for player in team_a) or any(player not in self.ratings for player in team_b):
            raise ValueError(f"플레이어가 등록되지 않았습니다: {team_a}, {team_b}")

        avg_rating_a = sum(self.ratings[player] for player in team_a) / len(team_a)
        avg_rating_b = sum(self.ratings[player] for player in team_b) / len(team_b)

        expected_a = 1 / (1 + 10 ** ((avg_rating_b - avg_rating_a) / 400))
        expected_b = 1 - expected_a

        delta_a = self.k * (result_a - expected_a)
        delta_b = self.k * ((1 - result_a) - expected_b)

        for player in team_a:
            self.pending_deltas.append((player, delta_a))

        for player in team_b:
            self.pending_deltas.append((player, delta_b))

        return abs(delta_a)

    def 게임(self, player_a, player_b, result_a):
        if player_a not in self.ratings or player_b not in self.ratings:
            raise ValueError(f"플레이어가 등록되지 않았습니다: {player_a}, {player_b}")

        rating_a = self.ratings[player_a]
        rating_b = self.ratings[player_b]

        expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
        delta = abs(self.k * (result_a - expected_a))
        delta_a = self.k * (result_a - expected_a)
        delta_b = -delta_a

        self.pending_deltas.append((player_a, delta_a))
        self.pending_deltas.append((player_b, delta_b))

        return abs(delta_a)

    def 승률(self):
        players = list(self.ratings.keys())
        winrates = []

        for i, player_a in enumerate(players):
            for j, player_b in enumerate(players):
                if i < j:
                    rating_a = self.ratings[player_a]
                    rating_b = self.ratings[player_b]
                    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
                    winrates.append((player_a, player_b, round(expected_a, 4)))

        return winrates

    def 랭킹(self):
        return sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)
        
    def 점수(self):
        return self.ratings

    def 종료(self):
        """
        대기 중인 델타를 한꺼번에 반영하고, 현재 점수를 출력.
        """
        for player, delta in self.pending_deltas:
            self.ratings[player] += delta

        self.pending_deltas.clear()
        
        return self.점수()
    
    def 초기화(self):
        return self.ratings.clear()
    
    
def 전적계산(검색결과):
    result = {"승리": sum(검색결과["점수1"] > 검색결과["점수2"]),
              "패배": sum(검색결과["점수1"] < 검색결과["점수2"]),
              "무승부": sum(검색결과["점수1"] == 검색결과["점수2"]),
              "전체": len(검색결과)
             }
    return result     