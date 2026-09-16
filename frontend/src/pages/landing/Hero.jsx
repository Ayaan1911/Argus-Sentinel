import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Github } from 'lucide-react';
import GlowOrb from '../../components/GlowOrb';
import { GITHUB_URL, DEMO_MODE, DEMO_URL, SHOW_DEMO_CTA } from './data';

export default function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/4">
        <GlowOrb size={620} chromatic animated />
      </div>

      <div className="relative max-w-4xl mx-auto px-6 pt-24 pb-28 sm:pt-32 sm:pb-36 text-center">
        {/* Contrast scrim. GlowOrb's chromatic mode paints a near-white core
            layer (`#ffffffcc` at its center) roughly where this whole text
            column sits, and it slowly drifts (animate-orb-drift) — so a
            contrast check at one fixed point in time understates the
            problem; the bright spot moves. One soft radial dark wash behind
            the text column, strongest at top-center where the orb's core
            actually is, fixes every element in the column at once instead
            of patching them one at a time. It sits between the orb and the
            text in DOM order, so it paints over the orb but under the copy. */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse 75% 70% at 50% 15%, rgba(10,14,20,0.78) 0%, rgba(10,14,20,0.42) 50%, transparent 78%)' }}
          aria-hidden="true"
        />

        <div className="relative">
          {/* Belt-and-suspenders on top of the broad scrim above: small
              dense text (11px, tracked-out) needs a guarantee, not just a
              improvement, so it also gets its own solid backing — the same
              `.glass-solid` treatment already used anywhere content must
              actually occlude what's behind it (see index.css). */}
          <div className="glass-solid inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.25em] font-bold text-textmut rounded-full px-4 py-1.5 mb-8">
            Open source · Self-hosted recon
          </div>

          <h1
            className="font-sans font-black text-5xl sm:text-6xl md:text-7xl tracking-tighter leading-[1.05] text-textpri"
            style={{ textShadow: '0 4px 28px rgba(0,0,0,0.55)' }}
          >
            Automated recon. Risk-scored findings.
            <br className="hidden sm:block" /> And <em className="font-serif italic font-normal text-accent">why</em> they matter.
          </h1>

          <p
            className="mt-8 text-lg sm:text-xl text-textmut max-w-2xl mx-auto leading-relaxed"
            style={{ textShadow: '0 2px 16px rgba(0,0,0,0.6)' }}
          >
            Argus Sentinel runs subfinder, httpx, nmap, and nuclei against a target in a real sequential
            pipeline, then correlates what they find into scored findings with an explained reasoning
            breakdown and audience-specific guidance — entirely on your own machine.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            {SHOW_DEMO_CTA && (
              // The external-link branch below is dormant today — SHOW_DEMO_CTA
              // currently equals DEMO_MODE, so whenever this renders, DEMO_URL
              // is always the internal "/dashboard". It's kept (not deleted)
              // because SHOW_DEMO_CTA is exactly the switch a future session
              // would flip to advertise a real public demo from a self-hosted
              // build too, at which point DEMO_URL's external branch goes live.
              <a
                href={DEMO_URL}
                {...(DEMO_MODE ? {} : { target: '_blank', rel: 'noreferrer' })}
                className="w-full sm:w-auto bg-accent text-background px-7 py-3.5 rounded-lg font-bold shadow-glow-accent hover:bg-accent/90 transition-all flex items-center justify-center gap-2"
              >
                Try the Demo <ArrowRight size={18} />
              </a>
            )}
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
              // bg-background/50 + backdrop-blur is a real (if small) scrim,
              // not just decoration — this button has no fill of its own,
              // so without it, it's exactly the same class of bug as the
              // badge above: text sitting on nothing but the orb.
              className="w-full sm:w-auto bg-background/50 backdrop-blur-md border border-bordercolor hover:border-accent/50 text-textpri px-7 py-3.5 rounded-lg font-bold transition-colors flex items-center justify-center gap-2"
            >
              <Github size={18} /> View on GitHub
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
