import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import EditorialNav from '../components/EditorialNav';
import client from '../api/client';
import '../editorial.css';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';
const SEVERITIES = ['critical', 'high', 'medium', 'low', 'informational'];

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : '—';
}

export default function Dashboard() {
  const { hash } = useLocation();
  const [scans, setScans] = useState([]);
  const [stats, setStats] = useState(null);
  const [summary, setSummary] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [summaryUnavailable, setSummaryUnavailable] = useState(false);
  const [comparisonUnavailable, setComparisonUnavailable] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [scansError, setScansError] = useState('');
  const [scansHasMore, setScansHasMore] = useState(false);
  const [loadingMoreScans, setLoadingMoreScans] = useState(false);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    setSummaryUnavailable(false);
    setComparisonUnavailable(false);
    Promise.all([client.get('/scans/?limit=50'), client.get('/scans/dashboard-stats')])
      .then(async ([scansRes, statsRes]) => {
        const recent = scansRes.data;
        let latestSummary = null;
        let latestComparison = null;
        let summaryFailed = false;
        let comparisonFailed = false;
        if (recent[0]?.status === 'completed') {
          const [summaryResult, diffResult] = await Promise.allSettled([
            client.get('/findings/scan/' + recent[0].id + '/summary'),
            client.get('/scans/' + recent[0].id + '/diff'),
          ]);
          if (summaryResult.status === 'fulfilled') latestSummary = summaryResult.value.data;
          if (diffResult.status === 'fulfilled') latestComparison = diffResult.value.data;
          summaryFailed = summaryResult.status === 'rejected';
          comparisonFailed = diffResult.status === 'rejected' && diffResult.reason?.response?.status !== 404;
        }
        if (!active) return;
        setScans(recent);
        setScansHasMore(recent.length === 50);
        setStats(statsRes.data);
        setSummary(latestSummary);
        setComparison(latestComparison);
        setSummaryUnavailable(summaryFailed);
        setComparisonUnavailable(comparisonFailed);
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setError('Could not load your scans. Check the API connection and try again.');
        setLoading(false);
      });
    return () => { active = false; };
  }, [retry]);

  const loadMoreScans = async () => {
    if (loadingMoreScans) return;
    setLoadingMoreScans(true);
    setScansError('');
    try {
      const res = await client.get('/scans/?limit=50&offset=' + scans.length);
      setScans(current => [...current, ...res.data]);
      setScansHasMore(res.data.length === 50);
    } catch {
      setScansError('Could not load older scans. Try again.');
    } finally {
      setLoadingMoreScans(false);
    }
  };

  const latest = scans[0];
  const diff = comparison?.summary;

  useEffect(() => {
    if (!loading && hash === '#history') document.getElementById('history')?.scrollIntoView();
  }, [loading, hash]);

  return (
    <div className="editorial editorial-workspace">
      <EditorialNav workspace />
      {DEMO_MODE && (
        <div className="editorial-demo">
          Public demo · scans are limited to the bundled Juice Shop target. <a href="https://github.com/Ayaan1911/Argus-Sentinel#readme" target="_blank" rel="noreferrer">Self-host to scan your own targets ↗</a>
        </div>
      )}
      <main className="editorial-wrap editorial-dashboard">
        <div className="editorial-dashboard-head">
          <div>
            <div className="editorial-kicker">Workspace / scan ledger</div>
            <h1>Overview of the evidence.</h1>
            <p>Start with the latest investigation, then follow each result back to its source.</p>
          </div>
          <Link className="editorial-button" to="/scan/new">Start a scan <span aria-hidden="true">↗</span></Link>
        </div>

        {loading ? (
          <p className="editorial-state" role="status">Loading your scans…</p>
        ) : error ? (
          <div className="editorial-state" role="alert">
            <p>{error}</p>
            <button type="button" className="editorial-button" onClick={() => setRetry(value => value + 1)}>Try again</button>
          </div>
        ) : !latest ? (
          <div className="editorial-state">
            <h2>No scans yet.</h2>
            <p>Run your first scan to build a record of findings and changes over time.</p>
            <Link className="editorial-text-link" to="/scan/new">Start your first scan ↗</Link>
          </div>
        ) : (
          <>
            <section aria-labelledby="latest-heading">
              <div className="editorial-section-line"><h2 id="latest-heading">Most recent investigation</h2><Link to={'/scan/' + latest.id}>Full report ↗</Link></div>
              <div className="editorial-latest">
                <div className="editorial-latest-target">
                  <div className="editorial-kicker">Target / latest run</div>
                  <strong>{latest.target}</strong>
                  <span>{formatDate(latest.created_at)} · <span className={'editorial-status editorial-status-' + latest.status}>{latest.status}</span></span>
                </div>
                <div className="editorial-metric"><strong>{latest.finding_count}</strong><span>Findings in this scan</span></div>
                {diff ? (
                  <>
                    <div className="editorial-metric"><strong>{diff.new}</strong><span>New since prior scan</span></div>
                    <div className="editorial-metric"><strong>{diff.resolved}</strong><span>No longer found</span></div>
                  </>
                ) : (
                  <div className="editorial-latest-note">
                    {latest.status !== 'completed'
                      ? 'Comparison is available after this scan completes.'
                      : comparisonUnavailable
                        ? 'Comparison is unavailable right now. Open the full report to retry.'
                        : 'No earlier completed scan of this target to compare.'}
                  </div>
                )}
              </div>
            </section>

            <div className="editorial-dashboard-grid">
              <section id="history" aria-labelledby="history-heading">
                <div className="editorial-section-line"><h2 id="history-heading">Scan ledger</h2><span>{stats?.total_scans ?? scans.length} recorded</span></div>
                <div className="editorial-table-wrap">
                  <table className="editorial-table">
                    <thead><tr><th scope="col">Target</th><th scope="col">Status</th><th scope="col">Findings</th><th scope="col">Started</th><th scope="col"><span className="sr-only">Report</span></th></tr></thead>
                    <tbody>
                      {scans.map(scan => (
                        <tr key={scan.id}>
                          <td data-label="Target"><strong>{scan.target}</strong></td>
                          <td data-label="Status"><span className={'editorial-status editorial-status-' + scan.status}>{scan.status}</span></td>
                          <td data-label="Findings">{scan.finding_count}</td>
                          <td data-label="Started">{formatDate(scan.created_at)}</td>
                          <td><Link to={'/scan/' + scan.id} aria-label={'View report for ' + scan.target + ' started ' + formatDate(scan.created_at)}>View ↗</Link></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {scansHasMore && <button className="editorial-load-more" type="button" onClick={loadMoreScans} disabled={loadingMoreScans}>{loadingMoreScans ? 'Loading…' : 'Load older scans ↓'}</button>}
                {scansError && <p className="editorial-error" role="alert">{scansError}</p>}
              </section>
              <section aria-labelledby="risk-heading">
                <div className="editorial-section-line"><h2 id="risk-heading">Latest scan, at a glance</h2><span>One run only</span></div>
                {summary ? (
                  <>
                    <div className="editorial-severity-list">
                      {SEVERITIES.map(severity => (
                        <div className="editorial-severity-row" key={severity}>
                          <span className={'editorial-severity-dot editorial-severity-' + severity} aria-hidden="true" />
                          <span>{severity === 'informational' ? 'Info' : severity}</span>
                          <strong>{summary.by_severity[severity] || 0}</strong>
                        </div>
                      ))}
                    </div>
                    {summary.top_findings?.length > 0 && (
                      <div className="editorial-top-findings">
                        <h3>Highest scored findings</h3>
                        {summary.top_findings.slice(0, 3).map(finding => (
                          <Link key={finding.id} to={'/scan/' + latest.id + '/finding/' + finding.id}>
                            <span>{finding.title}</span><strong>{finding.final_risk_score.toFixed(1)}</strong>
                          </Link>
                        ))}
                      </div>
                    )}
                  </>
                ) : (
                  <p className="editorial-muted">
                    {summaryUnavailable ? 'Could not load the risk summary. Open the full report to retry.' : 'The per-scan risk summary will appear when the completed report is available.'}
                  </p>
                )}
              </section>
            </div>
            <div className="editorial-dashboard-foot">
              Historical totals: {stats?.total_scans ?? scans.length} scans and {stats?.total_findings ?? 0} finding records. Repeated findings across scans are counted again.
            </div>
          </>
        )}
      </main>
    </div>
  );
}
