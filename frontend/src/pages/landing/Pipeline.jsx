import React from 'react';
import Reveal from '../../components/Reveal';
import { PIPELINE_STAGES } from './data';

export default function Pipeline() {
  return (
    <section className="max-w-5xl mx-auto px-6 py-24">
      <Reveal>
        <h2 className="font-sans font-black text-4xl sm:text-5xl tracking-tighter text-textpri text-center">
          How it <em className="font-serif italic font-normal text-accent">actually</em> works
        </h2>
        <p className="mt-4 text-textmut text-center max-w-xl mx-auto">
          Four real tools, run in order — each stage's output narrows what the next one scans.
        </p>
      </Reveal>

      <div className="mt-16 relative">
        {/* The chromatic ribbon as a literal connecting line — the one place
            in this section it's used, running behind all four stages. */}
        <div className="hidden md:block absolute top-6 left-[12.5%] right-[12.5%] h-0.5 bg-ribbon opacity-70 rounded-full" />

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 md:gap-6">
          {PIPELINE_STAGES.map((stage, i) => (
            <Reveal key={stage.name} delay={i * 100}>
              <div className="relative flex flex-col items-center text-center">
                <div className="relative z-10 w-12 h-12 rounded-full bg-surface border-2 border-accent/50 flex items-center justify-center font-mono font-black text-accent shadow-glow-accent mb-5">
                  {i + 1}
                </div>
                <div className="font-mono font-bold text-textpri text-lg tracking-tight">{stage.name}</div>
                <div className="text-[10px] uppercase tracking-[0.2em] font-bold text-accent mt-1">{stage.role}</div>
                <p className="text-sm text-textmut mt-3 leading-relaxed">{stage.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>

      <Reveal delay={200}>
        <p className="mt-14 text-center text-sm text-textmut max-w-2xl mx-auto">
          Each stage feeds the next — subfinder's discovered hosts go to httpx, httpx's confirmed-live
          hosts go to nmap, and nmap's scan targets (resolved to the real live URLs httpx already
          found) go to nuclei. A real sequential pipeline, not four scanners fired blind and independently.
        </p>
      </Reveal>
    </section>
  );
}
