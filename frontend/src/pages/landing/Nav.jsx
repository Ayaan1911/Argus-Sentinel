import React from 'react';
import { Link } from 'react-router-dom';
import { Github, ArrowRight } from 'lucide-react';
import { GITHUB_URL } from './data';

export default function Nav() {
  return (
    <header className="sticky top-0 z-20 backdrop-blur-xl bg-background/70 border-b border-white/[0.06]">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center shadow-glow-accent">
            <span className="text-accent font-black text-xl">A</span>
          </div>
          <span className="text-textpri font-black tracking-[0.18em] text-sm">SENTINEL</span>
        </Link>
        <div className="flex items-center gap-3">
          {/* Always /dashboard, unconditionally — doesn't need a
              VITE_DEMO_MODE branch. This build's own frontend bundle
              already has one fixed API key baked in at build time (demo or
              self-hosted, see data.js's DEMO_MODE comment for the full
              reasoning), so /dashboard is already the right, working
              destination in both modes: the locked demo in one, the real
              instance in the other. A real filled button, not a quiet text
              link — this is the nav's one clear primary action, same visual
              weight as Hero's "Try the Demo" CTA. */}
          <Link
            to="/dashboard"
            className="flex items-center gap-2 text-sm font-bold bg-accent text-background px-4 py-2 rounded-md shadow-glow-accent hover:bg-accent/90 transition-all"
          >
            Launch App <ArrowRight size={16} />
          </Link>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 text-sm font-semibold text-textpri border border-bordercolor hover:border-accent/50 rounded-md px-3 py-1.5 transition-colors"
          >
            <Github size={16} /> GitHub
          </a>
        </div>
      </div>
    </header>
  );
}
