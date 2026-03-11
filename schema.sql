PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS players (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  current_elo REAL NOT NULL DEFAULT 2000,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tournaments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  date TEXT NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('regular','always','friendly')),
  k INTEGER NOT NULL,
  base REAL NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'in_progress' CHECK(status IN ('in_progress','finished','canceled')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tournament_participants (
  tournament_id INTEGER NOT NULL,
  player_id INTEGER NOT NULL,
  PRIMARY KEY (tournament_id, player_id),
  FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
  FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tournament_snapshots (
  tournament_id INTEGER NOT NULL,
  player_id INTEGER NOT NULL,
  elo_snapshot REAL NOT NULL,
  PRIMARY KEY (tournament_id, player_id),
  FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
  FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS matches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tournament_id INTEGER NOT NULL,
  mode TEXT NOT NULL CHECK(mode IN ('singles','doubles')),
  team_a TEXT NOT NULL,
  team_b TEXT NOT NULL,
  score_a INTEGER NOT NULL,
  score_b INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS elo_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tournament_id INTEGER NOT NULL,
  player_id INTEGER NOT NULL,
  elo_before REAL NOT NULL,
  elo_after REAL NOT NULL,
  delta_total REAL NOT NULL,
  recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
  FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_matches_tournament ON matches(tournament_id, id);
CREATE INDEX IF NOT EXISTS idx_history_player ON elo_history(player_id, id);
CREATE INDEX IF NOT EXISTS idx_history_tournament ON elo_history(tournament_id);
