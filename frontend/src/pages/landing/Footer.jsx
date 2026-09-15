import React from 'react';
import { Github } from 'lucide-react';
import Reveal from '../../components/Reveal';
import { GITHUB_URL } from './data';

export default function Footer() {
  return (
    <footer className="border-t border-white/[0.06] mt-8">
      <Reveal>
        <div className="max-w-4xl mx-auto px-6 py-20 text-center">
          <h2 className="font-sans font-black text-3xl sm:text-4xl tracking-tighter text-textpri">
            Read the code. Run it <em className="font-serif italic font-normal text-accent">yourself</em>.
          </h2>
          <p className="mt-4 text-textmut max-w-md mx-auto">
            Argus Sentinel is free, MIT-licensed, and built for people who'd rather verify a claim than take it on faith.
          </p>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer"
            className="mt-8 inline-flex items-center gap-2 bg-accent text-background px-7 py-3.5 rounded-lg font-bold shadow-glow-accent hover:bg-accent/90 transition-all"
          >
            <Github size={18} /> View on GitHub
          </a>
          <div className="mt-10 text-xs text-textmut">
            MIT License · Argus Sentinel
          </div>
        </div>
      </Reveal>
    </footer>
  );
}
