import React from 'react';
import { Link } from 'react-router-dom';
import EditorialNav from '../components/EditorialNav';
import { AUDIENCES } from '../components/AudienceSelector';
import {
  DEMO_MODE, DIFF_EXAMPLE, EXAMPLE_FINDING, GITHUB_URL,
  INTELLIGENCE_TOTAL, PIPELINE_STAGES,
} from './landing/data';
import '../editorial.css';

export default function Landing() {
  return (
    <div className="editorial">
      <EditorialNav />
      <main>
        <section className="editorial-hero editorial-wrap">
          <div className="editorial-hero-copy">
            <div className="editorial-kicker">Field notes / 001 · Open-source reconnaissance</div>
            <h1>A clearer view of your <em>attack surface.</em></h1>
            <p>Four scanners, one traceable chain of evidence. See what was found, why it matters, and what changed since the last scan.</p>
            <div className="editorial-actions">
              <Link className="editorial-button" to="/dashboard">
                {DEMO_MODE ? 'Explore the demo' : 'Open your workspace'} <span aria-hidden="true">↗</span>
              </Link>
              <a className="editorial-text-link" href="#method">Read the method <span aria-hidden="true">↓</span></a>
            </div>
            <div className="editorial-hero-foot">Self-hosted · MIT licensed · Built for authorized testing</div>
          </div>
          <div className="editorial-report" id="evidence" aria-label="Recorded finding example">
            <div className="editorial-report-top"><span>RECORDED SCAN / FINDING</span><span>01 — 04</span></div>
            <div className="editorial-report-body">
              <div className="editorial-report-label">EVIDENCE, THEN INTERPRETATION</div>
              <div className="editorial-report-title">{EXAMPLE_FINDING.title}</div>
              <div className="editorial-report-meta"><span>{EXAMPLE_FINDING.type}</span><span>{EXAMPLE_FINDING.severity} severity</span><span>{EXAMPLE_FINDING.final_risk_score.toFixed(1)} / 10 risk</span></div>
              <p>{EXAMPLE_FINDING.technical_impact}</p>
              <div className="editorial-report-section">HOW ARGUS SCORED IT</div>
              {EXAMPLE_FINDING.reasoning_breakdown.map((step, index) => (
                <div className="editorial-report-row" key={step.label}>
                  <span>{String(index + 1).padStart(2, '0')} / {step.label}</span>
                  <strong>+{step.modifier.toFixed(1)}</strong>
                </div>
              ))}
            </div>
            <div className="editorial-report-caption">Actual finding from a recorded scan; target withheld.</div>
          </div>
        </section>

        <section className="editorial-section editorial-wrap" id="method">
          <div className="editorial-section-heading">
            <div className="editorial-kicker">The method / 01</div>
            <h2>Discovery, with a paper trail.</h2>
            <p>Each stage narrows what the next tool scans. The result is a sequence you can inspect, rather than four disconnected outputs.</p>
          </div>
          <div className="editorial-stages">
            {PIPELINE_STAGES.map((stage, index) => (
              <div className="editorial-stage" key={stage.name}>
                <span className="editorial-stage-number">{String(index + 1).padStart(2, '0')}</span>
                <div><strong>{stage.role}</strong><span>{stage.name}</span></div>
                <p>{stage.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="editorial-section editorial-section-tinted">
          <div className="editorial-wrap editorial-evidence-grid">
            <div>
              <div className="editorial-kicker">The evidence / 02</div>
              <h2>Follow the finding, not just the score.</h2>
              <p>Argus explains its risk calculation and keeps the original scanner evidence close. Guidance is written for the person reading it.</p>
              <div className="editorial-personas" aria-label="Supported audiences">
                {AUDIENCES.map(audience => <span key={audience.id}>{audience.label}</span>)}
              </div>
            </div>
            <div className="editorial-diff">
              <div className="editorial-report-top"><span>SCAN COMPARISON / RECORDED EXAMPLE</span><span>02 — 04</span></div>
              <div className="editorial-diff-body">
                <div className="editorial-diff-lead">What changed between scans?</div>
                <div className="editorial-diff-counts">
                  <div><strong>{DIFF_EXAMPLE.summary.new}</strong><span>New</span></div>
                  <div><strong>{DIFF_EXAMPLE.summary.resolved}</strong><span>Resolved</span></div>
                  <div><strong>{DIFF_EXAMPLE.summary.unchanged}</strong><span>Unchanged</span></div>
                </div>
                <div className="editorial-report-row"><span>{DIFF_EXAMPLE.new_findings[0].title}</span><b>NEW</b></div>
                <div className="editorial-report-row"><span>{DIFF_EXAMPLE.resolved_findings[0].title}</span><b>RESOLVED</b></div>
              </div>
              <div className="editorial-report-caption">Comparison from two completed Juice Shop scans. Scanner output can vary.</div>
            </div>
          </div>
        </section>

        <section className="editorial-section editorial-wrap editorial-open">
          <div>
            <div className="editorial-kicker">Open by design / 03</div>
            <h2>Run it yourself. Read the code.</h2>
          </div>
          <div>
            <p>Scan results stay in your own PostgreSQL database. The intelligence library contains {INTELLIGENCE_TOTAL} service, technology, and vulnerability entries you can inspect and extend.</p>
            <div className="editorial-open-links">
              <a className="editorial-text-link" href={GITHUB_URL} target="_blank" rel="noreferrer">Explore the GitHub repository <span aria-hidden="true">↗</span></a>
              <a className="editorial-text-link" href={GITHUB_URL + '/blob/main/argus-intelligence/CONTRIBUTING.md'} target="_blank" rel="noreferrer">Contribute an intelligence entry <span aria-hidden="true">↗</span></a>
            </div>
          </div>
        </section>
      </main>
      <footer className="editorial-footer"><div className="editorial-wrap"><span>ARGUS SENTINEL / MIT LICENSE</span><span>For targets you own or are authorized to test.</span></div></footer>
    </div>
  );
}
