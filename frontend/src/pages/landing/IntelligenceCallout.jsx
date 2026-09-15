import React from 'react';
import { BookOpen, ArrowRight, FileJson } from 'lucide-react';
import Reveal from '../../components/Reveal';
import { INTELLIGENCE_COUNTS, INTELLIGENCE_TOTAL, INTELLIGENCE_CONTRIBUTING_URL } from './data';

export default function IntelligenceCallout() {
  return (
    <section className="max-w-5xl mx-auto px-6 py-24">
      <Reveal>
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 text-accent mb-4">
              <BookOpen size={20} />
              <span className="text-[10px] uppercase tracking-[0.2em] font-bold">Intelligence Library</span>
            </div>
            <h2 className="font-sans font-black text-4xl sm:text-5xl tracking-tighter text-textpri leading-none">
              <span className="text-accent">{INTELLIGENCE_TOTAL}</span> real entries.
              <br />Every one <em className="font-serif italic font-normal">verified</em>.
            </h2>
            <p className="mt-6 text-textmut leading-relaxed">
              {INTELLIGENCE_COUNTS.services} services, {INTELLIGENCE_COUNTS.technologies} technologies, and{' '}
              {INTELLIGENCE_COUNTS.vulnerabilities} vulnerability classes — each one checked to actually
              affect scan output, not a placeholder with a name and a one-line description. A prior audit
              of this library removed 6 entries that looked complete but did nothing.
            </p>
            <a
              href={INTELLIGENCE_CONTRIBUTING_URL}
              target="_blank"
              rel="noreferrer"
              className="mt-6 inline-flex items-center gap-2 text-accent font-semibold hover:underline"
            >
              Add an entry — no Python or React required <ArrowRight size={16} />
            </a>
          </div>

          <div className="glass rounded-2xl p-8 flex flex-col items-center gap-4">
            <FileJson size={40} className="text-accent" />
            <p className="text-center text-textpri font-semibold">
              The single easiest way to contribute to Argus Sentinel doesn't touch Python or React.
            </p>
            <p className="text-center text-textmut text-sm leading-relaxed">
              It's a JSON file: pick a folder (<code className="font-mono text-accent">services/</code>,{' '}
              <code className="font-mono text-accent">technologies/</code>, or{' '}
              <code className="font-mono text-accent">vulnerabilities/</code>), fill in the required
              fields, and run the validator. That's the whole contribution.
            </p>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
