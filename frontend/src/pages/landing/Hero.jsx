import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Github } from 'lucide-react';
import GlowOrb from '../../components/GlowOrb';
import { GITHUB_URL } from './data';

// "Try the Demo" should point at the locked public demo instance once it's
// deployed (see DEMO_DEPLOYMENT.md — no live URL exists yet, this repo only
// documents how to stand one up). If this exact build IS that demo
// deployment (VITE_DEMO_MODE=true, same flag Layout.jsx/NewScan.jsx already
// key off), /dashboard already is the locked demo, so link there directly
// instead of a placeholder.
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';
// PLACEHOLDER — replace once DEMO_DEPLOYMENT.md has actually been run
// against a real host and a real domain exists.
const DEMO_URL = DEMO_MODE ? '/dashboard' : 'https://demo.argus-sentinel.dev';

export default function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/4">
        <GlowOrb size={620} chromatic animated />
      </div>

      <div className="relative max-w-4xl mx-auto px-6 pt-24 pb-28 sm:pt-32 sm:pb-36 text-center">
        <div className="inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.25em] font-bold text-textmut border border-bordercolor rounded-full px-4 py-1.5 mb-8">
          Open source · Self-hosted recon
        </div>

        <h1 className="font-sans font-black text-5xl sm:text-6xl md:text-7xl tracking-tighter leading-[1.05] text-textpri">
          Automated recon. Risk-scored findings.
          <br className="hidden sm:block" /> And <em className="font-serif italic font-normal text-accent">why</em> they matter.
        </h1>

        <p className="mt-8 text-lg sm:text-xl text-textmut max-w-2xl mx-auto leading-relaxed">
          Argus Sentinel runs subfinder, httpx, nmap, and nuclei against a target in a real sequential
          pipeline, then correlates what they find into scored findings with an explained reasoning
          breakdown and audience-specific guidance — entirely on your own machine.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <a
            href={DEMO_URL}
            {...(DEMO_MODE ? {} : { target: '_blank', rel: 'noreferrer' })}
            className="w-full sm:w-auto bg-accent text-background px-7 py-3.5 rounded-lg font-bold shadow-glow-accent hover:bg-accent/90 transition-all flex items-center justify-center gap-2"
          >
            Try the Demo <ArrowRight size={18} />
          </a>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer"
            className="w-full sm:w-auto border border-bordercolor hover:border-accent/50 text-textpri px-7 py-3.5 rounded-lg font-bold transition-colors flex items-center justify-center gap-2"
          >
            <Github size={18} /> View on GitHub
          </a>
        </div>
      </div>
    </section>
  );
}
