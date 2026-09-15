import React from 'react';
import { Brain, Users, GitCompare, Plus, CheckCheck } from 'lucide-react';
import Reveal from '../../components/Reveal';
import SeverityBadge from '../../components/SeverityBadge';
import RiskScore from '../../components/RiskScore';
import ReasoningBreakdown from '../../components/ReasoningBreakdown';
import { AUDIENCES } from '../../components/AudienceSelector';
import { EXAMPLE_FINDING, DIFF_EXAMPLE } from './data';

function SectionHeading({ icon: Icon, kicker, children }) {
  return (
    <div className="flex items-center gap-3 mb-6">
      <div className="p-2.5 bg-accent/10 text-accent rounded-lg shrink-0">
        <Icon size={20} />
      </div>
      <div>
        <div className="text-[10px] uppercase tracking-[0.2em] font-bold text-accent">{kicker}</div>
        <h3 className="font-sans font-black text-2xl sm:text-3xl tracking-tight text-textpri">{children}</h3>
      </div>
    </div>
  );
}

export default function Differentiators() {
  return (
    <section className="max-w-5xl mx-auto px-6 py-24">
      <Reveal>
        <h2 className="font-sans font-black text-4xl sm:text-5xl tracking-tighter text-textpri text-center">
          What makes it <em className="font-serif italic font-normal text-accent">different</em>
        </h2>
        <p className="mt-4 text-textmut text-center max-w-xl mx-auto">
          Three things most recon tools don't do — shown here with real output, not mockups.
        </p>
      </Reveal>

      {/* 1. The reasoning engine — a real finding, rendered with the actual
          components the dashboard uses (RiskScore, ReasoningBreakdown), not
          a redrawn approximation. */}
      <Reveal delay={100} className="mt-16">
        <SectionHeading icon={Brain} kicker="The reasoning engine">
          Every score comes with its reasoning
        </SectionHeading>
        <p className="text-textmut leading-relaxed mb-6">
          Findings don't just get a severity label — they get an explained score. Here's a real one,
          pulled straight from an actual scan (the target isn't shown; the score and reasoning are
          exactly what Argus produced):
        </p>
        <div className="glass rounded-2xl p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row gap-6 items-start">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-3">
                <SeverityBadge severity={EXAMPLE_FINDING.severity} />
                <span className="text-textmut uppercase tracking-[0.18em] text-[10px] font-bold border border-bordercolor px-2 py-1 rounded bg-surface">
                  {EXAMPLE_FINDING.type}
                </span>
              </div>
              <h4 className="text-xl font-black text-textpri tracking-tight font-mono">{EXAMPLE_FINDING.title}</h4>
              <p className="text-textmut text-sm mt-2 leading-relaxed">{EXAMPLE_FINDING.technical_impact}</p>
            </div>
            <div className="shrink-0 mx-auto">
              <RiskScore score={EXAMPLE_FINDING.final_risk_score} size={110} />
            </div>
          </div>
          <div className="mt-6">
            <ReasoningBreakdown breakdown={EXAMPLE_FINDING.reasoning_breakdown} />
          </div>
        </div>
      </Reveal>

      {/* 2. Audience-specific guidance */}
      <Reveal delay={100} className="mt-20">
        <SectionHeading icon={Users} kicker="Guidance that matches the reader">
          The same finding, explained differently
        </SectionHeading>
        <p className="text-textmut leading-relaxed mb-6">
          A student needs the concept explained. A pentester needs the exploit path. Every finding
          carries guidance written for all five, and you pick who's reading:
        </p>
        <div className="flex flex-wrap gap-2">
          {AUDIENCES.map((aud) => (
            <span
              key={aud.id}
              className="px-4 py-2 rounded-lg bg-card border border-bordercolor text-textpri font-semibold text-sm"
            >
              {aud.label}
            </span>
          ))}
        </div>
      </Reveal>

      {/* 3. Scan-history diffing — a real juice-shop diff. */}
      <Reveal delay={100} className="mt-20">
        <SectionHeading icon={GitCompare} kicker="It remembers the last scan">
          NEW findings jump out, automatically
        </SectionHeading>
        <p className="text-textmut leading-relaxed mb-6">
          Every scan is diffed against the one before it —{' '}
          <span className="font-mono text-textpri font-bold">{DIFF_EXAMPLE.summary.new} new</span>,{' '}
          <span className="font-mono text-textpri font-bold">{DIFF_EXAMPLE.summary.resolved} resolved</span>,{' '}
          <span className="font-mono text-textpri font-bold">{DIFF_EXAMPLE.summary.unchanged} unchanged</span>{' '}
          below is real, from two scans of the bundled demo target a few hours apart. When a finding's
          risk score shifts between scans instead of appearing or disappearing outright — say, a port
          that was internal becomes internet-facing — it's marked CHANGED with the old score shown
          right next to the new one.
        </p>
        <div className="grid sm:grid-cols-2 gap-3">
          <div className="space-y-2">
            {DIFF_EXAMPLE.new_findings.map((f) => (
              <div
                key={f.title}
                className="glass shadow-glow-new flex items-center justify-between gap-3 px-4 py-3 rounded-lg border-l-4 border-l-violet-400"
              >
                <span className="text-sm font-semibold text-textpri truncate">{f.title}</span>
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-mono font-black tracking-[0.1em] border bg-violet-400/20 text-violet-200 border-violet-400/60 shrink-0">
                  <Plus size={11} strokeWidth={3} /> NEW
                </span>
              </div>
            ))}
          </div>
          <div className="space-y-2">
            {DIFF_EXAMPLE.resolved_findings.map((f) => (
              <div
                key={f.title}
                className="bg-card/40 flex items-center justify-between gap-3 px-4 py-3 rounded-lg border border-bordercolor border-l-4 border-l-bordercolor opacity-60"
              >
                <span className="text-sm font-semibold text-textpri truncate line-through decoration-textmut">{f.title}</span>
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-mono font-black tracking-[0.1em] border bg-surface text-textmut border-bordercolor shrink-0">
                  <CheckCheck size={11} strokeWidth={3} /> RESOLVED
                </span>
              </div>
            ))}
          </div>
        </div>
      </Reveal>
    </section>
  );
}
