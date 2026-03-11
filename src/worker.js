const TYPE_TO_K = { regular: 200, always: 100, friendly: 0 };

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
      'access-control-allow-headers': 'content-type',
    },
  });

const err = (message, status = 400) => json({ error: message }, status);

const parseBody = async (request) => {
  try {
    return await request.json();
  } catch {
    return {};
  }
};

const expectedScore = (a, b) => 1 / (1 + 10 ** ((b - a) / 400));
const avg = (values) => values.reduce((acc, v) => acc + v, 0) / values.length;
const normalizeTeam = (team) => [...new Set((team || []).map((v) => Number(v)).filter(Boolean))];
const safeJSON = (value) => {
  try {
    return JSON.parse(value);
  } catch {
    return [];
  }
};

function applyMatchDelta(state, match, k, base) {
  const teamA = safeJSON(match.team_a);
  const teamB = safeJSON(match.team_b);
  const eloA = avg(teamA.map((id) => state[id] ?? 2000));
  const eloB = avg(teamB.map((id) => state[id] ?? 2000));
  const eA = expectedScore(eloA, eloB);
  const sA = match.score_a > match.score_b ? 1 : 0;
  const deltaTeamA = k * (sA - eA) + (sA === 1 ? base : -base);
  const deltaTeamB = -k * (sA - eA) + (sA === 0 ? base : -base);
  const deltaPerA = deltaTeamA / teamA.length;
  const deltaPerB = deltaTeamB / teamB.length;

  for (const id of teamA) state[id] = (state[id] ?? 2000) + deltaPerA;
  for (const id of teamB) state[id] = (state[id] ?? 2000) + deltaPerB;
}

async function getPlayersMap(env) {
  const rows = await env.DB.prepare('SELECT id, name, current_elo, is_active FROM players').all();
  return Object.fromEntries((rows.results || []).map((p) => [p.id, p]));
}

async function getTournament(env, tournamentId) {
  return env.DB.prepare('SELECT * FROM tournaments WHERE id = ?').bind(tournamentId).first();
}

async function getParticipants(env, tournamentId) {
  const rows = await env.DB.prepare('SELECT player_id FROM tournament_participants WHERE tournament_id = ?').bind(tournamentId).all();
  return new Set((rows.results || []).map((r) => r.player_id));
}

async function listPlayers(env) {
  const rows = await env.DB.prepare(
    'SELECT id, name, current_elo AS currentElo, created_at AS createdAt, is_active AS isActive FROM players ORDER BY current_elo DESC, id ASC'
  ).all();
  return json(rows.results || []);
}

async function createPlayer(env, request) {
  const body = await parseBody(request);
  const name = (body.name || '').trim();
  const initialElo = Number(body.initialElo);
  if (!name) return err('name is required');

  let seed = 2000;
  if (Number.isFinite(initialElo)) {
    seed = initialElo;
  } else {
    const row = await env.DB.prepare('SELECT AVG(current_elo) AS avgElo FROM players WHERE is_active = 1').first();
    if (Number.isFinite(row?.avgElo)) seed = row.avgElo;
  }

  try {
    const result = await env.DB.prepare('INSERT INTO players(name, current_elo) VALUES(?, ?)').bind(name, seed).run();
    return json({ id: result.meta.last_row_id, name, currentElo: seed }, 201);
  } catch {
    return err('player already exists', 409);
  }
}

async function updatePlayer(env, playerId, request) {
  const body = await parseBody(request);
  const name = typeof body.name === 'string' ? body.name.trim() : null;
  const isActive = body.isActive;
  const currentElo = Number(body.currentElo);

  const player = await env.DB.prepare('SELECT id FROM players WHERE id = ?').bind(playerId).first();
  if (!player) return err('player not found', 404);

  if (name) await env.DB.prepare('UPDATE players SET name = ? WHERE id = ?').bind(name, playerId).run();
  if (typeof isActive === 'boolean') await env.DB.prepare('UPDATE players SET is_active = ? WHERE id = ?').bind(isActive ? 1 : 0, playerId).run();
  if (Number.isFinite(currentElo)) await env.DB.prepare('UPDATE players SET current_elo = ? WHERE id = ?').bind(currentElo, playerId).run();

  const updated = await env.DB.prepare(
    'SELECT id, name, current_elo AS currentElo, is_active AS isActive, created_at AS createdAt FROM players WHERE id = ?'
  ).bind(playerId).first();
  return json(updated);
}

async function listTournaments(env) {
  const rows = await env.DB.prepare(
    'SELECT id, name, date, type, k, base, status, created_at AS createdAt FROM tournaments ORDER BY id DESC'
  ).all();
  return json(rows.results || []);
}

async function createTournament(env, request) {
  const body = await parseBody(request);
  const name = (body.name || '').trim();
  const date = body.date || new Date().toISOString().slice(0, 10);
  const type = body.type || 'always';
  const k = TYPE_TO_K[type];
  const base = Number(body.base ?? 0);
  const participantIds = normalizeTeam(body.participantIds);

  if (!name || !Number.isFinite(k)) return err('invalid payload');
  if (participantIds.length < 2) return err('at least 2 participants required');

  const players = await getPlayersMap(env);
  for (const id of participantIds) {
    if (!players[id]) return err(`player ${id} not found`, 404);
  }

  const created = await env.DB.prepare('INSERT INTO tournaments(name, date, type, k, base) VALUES(?, ?, ?, ?, ?)')
    .bind(name, date, type, k, base)
    .run();
  const tournamentId = created.meta.last_row_id;

  for (const playerId of participantIds) {
    await env.DB.prepare('INSERT INTO tournament_participants(tournament_id, player_id) VALUES(?, ?)').bind(tournamentId, playerId).run();
    await env.DB.prepare(
      'INSERT INTO tournament_snapshots(tournament_id, player_id, elo_snapshot) SELECT ?, id, current_elo FROM players WHERE id = ?'
    ).bind(tournamentId, playerId).run();
  }

  return json({ id: tournamentId, name, date, type, k, base, status: 'in_progress', participantIds }, 201);
}

async function updateTournament(env, tournamentId, request) {
  const t = await getTournament(env, tournamentId);
  if (!t) return err('tournament not found', 404);
  if (t.status !== 'in_progress') return err('only in_progress tournament can be updated', 409);

  const body = await parseBody(request);
  const name = (body.name || t.name).trim();
  const date = body.date || t.date;
  const type = body.type || t.type;
  const k = TYPE_TO_K[type];
  const base = Number(body.base ?? t.base);
  if (!name || !Number.isFinite(k)) return err('invalid payload');

  const matchCount = await env.DB.prepare('SELECT COUNT(*) AS cnt FROM matches WHERE tournament_id = ?').bind(tournamentId).first();
  if (type !== t.type && Number(matchCount?.cnt || 0) > 0) return err('cannot change type after matches are recorded', 409);

  await env.DB.prepare('UPDATE tournaments SET name = ?, date = ?, type = ?, k = ?, base = ? WHERE id = ?')
    .bind(name, date, type, k, base, tournamentId)
    .run();

  return json({ id: tournamentId, name, date, type, k, base, status: 'in_progress' });
}

async function getTournamentDetail(env, tournamentId) {
  const tournament = await getTournament(env, tournamentId);
  if (!tournament) return err('tournament not found', 404);

  const participants = await env.DB.prepare(
    `SELECT p.id, p.name, ts.elo_snapshot AS snapshotElo, p.current_elo AS currentElo
     FROM tournament_participants tp
     JOIN players p ON p.id = tp.player_id
     LEFT JOIN tournament_snapshots ts ON ts.tournament_id = tp.tournament_id AND ts.player_id = tp.player_id
     WHERE tp.tournament_id = ? ORDER BY p.name`
  ).bind(tournamentId).all();

  return json({ ...tournament, participants: participants.results || [] });
}

async function addMatch(env, request, tournamentId) {
  const tournament = await getTournament(env, tournamentId);
  if (!tournament) return err('tournament not found', 404);
  if (tournament.status !== 'in_progress') return err('tournament is not in progress', 409);

  const body = await parseBody(request);
  const mode = body.mode === 'doubles' ? 'doubles' : 'singles';
  const teamA = normalizeTeam(body.teamA);
  const teamB = normalizeTeam(body.teamB);
  const scoreA = Number(body.scoreA);
  const scoreB = Number(body.scoreB);

  if (!Number.isInteger(scoreA) || !Number.isInteger(scoreB) || scoreA === scoreB) return err('invalid score');
  if (!teamA.length || !teamB.length || teamA.some((id) => teamB.includes(id))) return err('invalid teams');
  if (mode === 'singles' && (teamA.length !== 1 || teamB.length !== 1)) return err('singles requires 1v1');
  if (mode === 'doubles' && (teamA.length !== 2 || teamB.length !== 2)) return err('doubles requires 2v2');

  const participants = await getParticipants(env, tournamentId);
  for (const id of [...teamA, ...teamB]) {
    if (!participants.has(id)) return err(`player ${id} is not a tournament participant`, 400);
  }

  const inserted = await env.DB.prepare(
    'INSERT INTO matches(tournament_id, mode, team_a, team_b, score_a, score_b) VALUES(?, ?, ?, ?, ?, ?)'
  ).bind(tournamentId, mode, JSON.stringify(teamA), JSON.stringify(teamB), scoreA, scoreB).run();

  return json({ id: inserted.meta.last_row_id, tournamentId, mode, teamA, teamB, scoreA, scoreB }, 201);
}

async function listMatches(env, tournamentId) {
  const rows = await env.DB.prepare(
    'SELECT id, mode, team_a AS teamA, team_b AS teamB, score_a AS scoreA, score_b AS scoreB, created_at AS createdAt FROM matches WHERE tournament_id = ? ORDER BY id DESC'
  ).bind(tournamentId).all();

  return json((rows.results || []).map((m) => ({ ...m, teamA: safeJSON(m.teamA), teamB: safeJSON(m.teamB) })));
}

async function deleteMatch(env, tournamentId, matchId) {
  const tournament = await getTournament(env, tournamentId);
  if (!tournament) return err('tournament not found', 404);
  if (tournament.status !== 'in_progress') return err('can only delete matches from in_progress tournaments', 409);

  const deleted = await env.DB.prepare('DELETE FROM matches WHERE id = ? AND tournament_id = ?').bind(matchId, tournamentId).run();
  if (!deleted.meta.changes) return err('match not found', 404);
  return json({ ok: true });
}

async function tournamentAnalysis(env, tournamentId) {
  const participants = await env.DB.prepare(
    `SELECT p.id, p.name, ts.elo_snapshot AS elo
     FROM tournament_participants tp
     JOIN players p ON p.id = tp.player_id
     JOIN tournament_snapshots ts ON ts.tournament_id = tp.tournament_id AND ts.player_id = tp.player_id
     WHERE tp.tournament_id = ?`
  ).bind(tournamentId).all();

  const list = participants.results || [];
  const pairwise = [];
  for (let i = 0; i < list.length; i += 1) {
    for (let j = i + 1; j < list.length; j += 1) {
      const a = list[i];
      const b = list[j];
      pairwise.push({
        aId: a.id,
        bId: b.id,
        aName: a.name,
        bName: b.name,
        aWinRate: Number((expectedScore(a.elo, b.elo) * 100).toFixed(2)),
      });
    }
  }

  return json({ participants: list, pairwise });
}

async function getStandings(env, tournamentId) {
  const tournament = await getTournament(env, tournamentId);
  if (!tournament) return err('tournament not found', 404);

  const players = await env.DB.prepare(
    `SELECT p.id, p.name, ts.elo_snapshot
     FROM tournament_participants tp
     JOIN players p ON p.id = tp.player_id
     JOIN tournament_snapshots ts ON ts.tournament_id = tp.tournament_id AND ts.player_id = tp.player_id
     WHERE tp.tournament_id = ?`
  ).bind(tournamentId).all();
  const matches = await env.DB.prepare('SELECT team_a, team_b, score_a, score_b FROM matches WHERE tournament_id = ? ORDER BY id ASC').bind(tournamentId).all();

  const table = {};
  const eloState = {};
  for (const p of players.results || []) {
    table[p.id] = { playerId: p.id, name: p.name, wins: 0, losses: 0, matches: 0, snapshotElo: p.elo_snapshot, provisionalElo: p.elo_snapshot };
    eloState[p.id] = p.elo_snapshot;
  }

  for (const m of matches.results || []) {
    const teamA = safeJSON(m.team_a);
    const teamB = safeJSON(m.team_b);
    const aWin = m.score_a > m.score_b;

    for (const id of teamA) {
      table[id].matches += 1;
      table[id][aWin ? 'wins' : 'losses'] += 1;
    }
    for (const id of teamB) {
      table[id].matches += 1;
      table[id][aWin ? 'losses' : 'wins'] += 1;
    }

    applyMatchDelta(eloState, m, tournament.k, tournament.base);
  }

  for (const row of Object.values(table)) row.provisionalElo = Number(eloState[row.playerId].toFixed(2));
  const standings = Object.values(table).sort((a, b) => b.wins - a.wins || b.provisionalElo - a.provisionalElo);
  return json(standings);
}

async function finalizeTournament(env, tournamentId) {
  const tournament = await getTournament(env, tournamentId);
  if (!tournament) return err('tournament not found', 404);
  if (tournament.status !== 'in_progress') return err('tournament is not in progress', 409);

  const snaps = await env.DB.prepare('SELECT player_id, elo_snapshot FROM tournament_snapshots WHERE tournament_id = ?').bind(tournamentId).all();
  const matches = await env.DB.prepare('SELECT team_a, team_b, score_a, score_b FROM matches WHERE tournament_id = ? ORDER BY id ASC').bind(tournamentId).all();

  const state = {};
  for (const row of snaps.results || []) state[row.player_id] = row.elo_snapshot;
  for (const match of matches.results || []) applyMatchDelta(state, match, tournament.k, tournament.base);

  for (const row of snaps.results || []) {
    const after = state[row.player_id] ?? row.elo_snapshot;
    const delta = after - row.elo_snapshot;
    await env.DB.prepare('UPDATE players SET current_elo = ? WHERE id = ?').bind(after, row.player_id).run();
    await env.DB.prepare(
      'INSERT INTO elo_history(tournament_id, player_id, elo_before, elo_after, delta_total) VALUES(?, ?, ?, ?, ?)'
    ).bind(tournamentId, row.player_id, row.elo_snapshot, after, delta).run();
  }

  await env.DB.prepare('UPDATE tournaments SET status = ? WHERE id = ?').bind('finished', tournamentId).run();
  return json({ ok: true, tournamentId, playerCount: (snaps.results || []).length, matchCount: (matches.results || []).length });
}

async function cancelTournament(env, tournamentId) {
  const tournament = await getTournament(env, tournamentId);
  if (!tournament) return err('tournament not found', 404);
  if (tournament.status !== 'in_progress') return err('tournament is not in progress', 409);
  await env.DB.prepare('UPDATE tournaments SET status = ? WHERE id = ?').bind('canceled', tournamentId).run();
  return json({ ok: true, tournamentId, status: 'canceled' });
}

async function playerHistory(env, playerId) {
  const player = await env.DB.prepare('SELECT id, name, current_elo AS currentElo FROM players WHERE id = ?').bind(playerId).first();
  if (!player) return err('player not found', 404);

  const rows = await env.DB.prepare(
    `SELECT eh.id, eh.elo_before AS eloBefore, eh.elo_after AS eloAfter, eh.delta_total AS deltaTotal,
            eh.recorded_at AS recordedAt, t.id AS tournamentId, t.name AS tournamentName, t.date AS tournamentDate
       FROM elo_history eh
       JOIN tournaments t ON t.id = eh.tournament_id
      WHERE eh.player_id = ?
      ORDER BY eh.id DESC`
  ).bind(playerId).all();

  return json({ player, history: rows.results || [] });
}

function accumulateMatchStats(matches) {
  const stats = {};
  const add = (id, mode, won) => {
    if (!stats[id]) stats[id] = { matches: 0, wins: 0, losses: 0, singles: { matches: 0, wins: 0 }, doubles: { matches: 0, wins: 0 } };
    stats[id].matches += 1;
    stats[id][won ? 'wins' : 'losses'] += 1;
    stats[id][mode].matches += 1;
    if (won) stats[id][mode].wins += 1;
  };

  for (const m of matches) {
    const aWin = m.score_a > m.score_b;
    const teamA = safeJSON(m.team_a);
    const teamB = safeJSON(m.team_b);
    for (const id of teamA) add(id, m.mode, aWin);
    for (const id of teamB) add(id, m.mode, !aWin);
  }
  return stats;
}

async function overviewStats(env) {
  const playersRows = await env.DB.prepare('SELECT id, name, current_elo AS currentElo FROM players WHERE is_active = 1').all();
  const tournamentRows = await env.DB.prepare('SELECT id, name, date, status, type FROM tournaments ORDER BY id DESC').all();
  const matchRows = await env.DB.prepare('SELECT * FROM matches').all();
  const stats = accumulateMatchStats(matchRows.results || []);

  const topByElo = (playersRows.results || []).sort((a, b) => b.currentElo - a.currentElo).slice(0, 10);
  const topWinrate = (playersRows.results || [])
    .map((p) => {
      const s = stats[p.id] || { matches: 0, wins: 0 };
      return { playerId: p.id, name: p.name, matches: s.matches, winRate: s.matches ? Number(((s.wins / s.matches) * 100).toFixed(2)) : 0 };
    })
    .filter((r) => r.matches > 0)
    .sort((a, b) => b.winRate - a.winRate || b.matches - a.matches)
    .slice(0, 10);

  return json({
    counts: {
      players: (playersRows.results || []).length,
      tournaments: (tournamentRows.results || []).length,
      matches: (matchRows.results || []).length,
    },
    topByElo,
    topWinrate,
    tournaments: tournamentRows.results || [],
  });
}

async function resetAll(env) {
  const tables = ['elo_history', 'matches', 'tournament_snapshots', 'tournament_participants', 'tournaments', 'players'];
  for (const table of tables) {
    await env.DB.prepare(`DELETE FROM ${table}`).run();
  }
  return json({ ok: true });
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return json({ ok: true });

    const url = new URL(request.url);
    const { pathname } = url;

    if (request.method === 'GET' && pathname === '/api/health') return json({ ok: true });

    if (request.method === 'GET' && pathname === '/api/players') return listPlayers(env);
    if (request.method === 'POST' && pathname === '/api/players') return createPlayer(env, request);
    const pEdit = pathname.match(/^\/api\/players\/(\d+)$/);
    if (request.method === 'PATCH' && pEdit) return updatePlayer(env, Number(pEdit[1]), request);

    if (request.method === 'GET' && pathname === '/api/tournaments') return listTournaments(env);
    if (request.method === 'POST' && pathname === '/api/tournaments') return createTournament(env, request);

    const tDetail = pathname.match(/^\/api\/tournaments\/(\d+)$/);
    if (request.method === 'GET' && tDetail) return getTournamentDetail(env, Number(tDetail[1]));
    if (request.method === 'PATCH' && tDetail) return updateTournament(env, Number(tDetail[1]), request);

    const tMatches = pathname.match(/^\/api\/tournaments\/(\d+)\/matches$/);
    if (request.method === 'GET' && tMatches) return listMatches(env, Number(tMatches[1]));
    if (request.method === 'POST' && tMatches) return addMatch(env, request, Number(tMatches[1]));

    const tMatchDelete = pathname.match(/^\/api\/tournaments\/(\d+)\/matches\/(\d+)$/);
    if (request.method === 'DELETE' && tMatchDelete) return deleteMatch(env, Number(tMatchDelete[1]), Number(tMatchDelete[2]));

    const tStandings = pathname.match(/^\/api\/tournaments\/(\d+)\/standings$/);
    if (request.method === 'GET' && tStandings) return getStandings(env, Number(tStandings[1]));

    const tAnalysis = pathname.match(/^\/api\/tournaments\/(\d+)\/analysis$/);
    if (request.method === 'GET' && tAnalysis) return tournamentAnalysis(env, Number(tAnalysis[1]));

    const tFinalize = pathname.match(/^\/api\/tournaments\/(\d+)\/finalize$/);
    if (request.method === 'POST' && tFinalize) return finalizeTournament(env, Number(tFinalize[1]));

    const tCancel = pathname.match(/^\/api\/tournaments\/(\d+)\/cancel$/);
    if (request.method === 'POST' && tCancel) return cancelTournament(env, Number(tCancel[1]));

    const ph = pathname.match(/^\/api\/history\/players\/(\d+)$/);
    if (request.method === 'GET' && ph) return playerHistory(env, Number(ph[1]));

    if (request.method === 'GET' && pathname === '/api/stats/overview') return overviewStats(env);
    if (request.method === 'POST' && pathname === '/api/admin/reset') return resetAll(env);

    if (env.ASSETS) return env.ASSETS.fetch(request);
    return err('not found', 404);
  },
};
