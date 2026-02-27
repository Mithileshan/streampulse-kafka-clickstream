import 'dotenv/config';
import express from 'express';
import pg from 'pg';

const { Pool } = pg;

const pool = new Pool({
  host:     process.env['POSTGRES_HOST']     ?? 'localhost',
  port:     Number(process.env['POSTGRES_PORT'] ?? 5433),
  database: process.env['POSTGRES_DB']       ?? 'streampulse',
  user:     process.env['POSTGRES_USER']     ?? 'streampulse',
  password: process.env['POSTGRES_PASSWORD'] ?? 'streampulse',
});

const app  = express();
const PORT = process.env['PORT'] ?? 4000;

// ── Health ────────────────────────────────────────────────────────────────────
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// ── GET /stats/top ────────────────────────────────────────────────────────────
app.get('/stats/top', async (_req, res) => {
  const { rows } = await pool.query(`
    SELECT short_code, total_clicks, last_seen
    FROM   click_aggregates
    ORDER  BY total_clicks DESC
    LIMIT  10
  `);
  res.json(rows);
});

// ── GET /stats/trending ───────────────────────────────────────────────────────
app.get('/stats/trending', async (req, res) => {
  const hours = Number(req.query['hours'] ?? 24);
  const { rows } = await pool.query(`
    SELECT   short_code, COUNT(*) AS clicks
    FROM     click_events
    WHERE    occurred_at > NOW() - ($1 || ' hours')::INTERVAL
    GROUP BY short_code
    ORDER BY clicks DESC
    LIMIT    10
  `, [hours]);
  res.json(rows);
});

// ── GET /stats/:shortCode ─────────────────────────────────────────────────────
app.get('/stats/:shortCode', async (req, res) => {
  const { shortCode } = req.params;

  const [agg, last24h, topReferrers] = await Promise.all([
    pool.query(
      `SELECT short_code, total_clicks, last_seen
       FROM   click_aggregates
       WHERE  short_code = $1`,
      [shortCode]
    ),
    pool.query(
      `SELECT COUNT(*) AS clicks
       FROM   click_events
       WHERE  short_code = $1
       AND    occurred_at > NOW() - INTERVAL '24 hours'`,
      [shortCode]
    ),
    pool.query(
      `SELECT   referrer, COUNT(*) AS clicks
       FROM     click_events
       WHERE    short_code = $1 AND referrer != ''
       GROUP BY referrer
       ORDER BY clicks DESC
       LIMIT    5`,
      [shortCode]
    ),
  ]);

  if (agg.rows.length === 0) {
    res.status(404).json({ error: { code: 'NOT_FOUND', message: `No stats for ${shortCode}` } });
    return;
  }

  res.json({
    shortCode:    agg.rows[0].short_code,
    totalClicks:  Number(agg.rows[0].total_clicks),
    last24Hours:  Number(last24h.rows[0].clicks),
    lastSeen:     agg.rows[0].last_seen,
    topReferrers: topReferrers.rows.map(r => ({
      referrer: r.referrer,
      clicks:   Number(r.clicks),
    })),
  });
});

app.listen(PORT, () => {
  console.log(`StreamPulse Analytics API running on http://localhost:${PORT}`);
});
