import React from 'react';
import { ShieldCheck, EyeOff, Database } from 'lucide-react';
import Reveal from '../../components/Reveal';

const POINTS = [
  {
    icon: EyeOff,
    title: 'No telemetry, no phone-home',
    desc: "There's no analytics call, no crash reporter, no hosted backend collecting your recon data anywhere in this codebase — check for yourself.",
  },
  {
    icon: Database,
    title: 'Your data stays in your Postgres',
    desc: 'Scan results, findings, and history live in the database container you run. Nothing is synced anywhere else.',
  },
  {
    icon: ShieldCheck,
    title: 'The only network calls are the ones you ask for',
    desc: "subfinder, httpx, nmap, and nuclei only ever talk to the target you submit — there's no third leg back to us.",
  },
];

export default function Privacy() {
  return (
    <section className="max-w-5xl mx-auto px-6 py-24">
      <Reveal>
        <div className="glass rounded-2xl p-8 sm:p-12">
          <h2 className="font-sans font-black text-4xl sm:text-5xl tracking-tighter text-textpri text-center">
            Self-hosted. <em className="font-serif italic font-normal text-accent">Not</em> hosted.
          </h2>
          <p className="mt-4 text-textmut text-center max-w-xl mx-auto leading-relaxed">
            Nothing you scan ever leaves your machine. There's no hosted version of Argus Sentinel with
            your data in it — and since it's open source, that's not a promise you have to take on faith.
          </p>

          <div className="mt-12 grid sm:grid-cols-3 gap-8">
            {POINTS.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="text-center">
                <div className="inline-flex p-3 bg-accent/10 text-accent rounded-lg mb-4">
                  <Icon size={22} />
                </div>
                <div className="font-bold text-textpri mb-2">{title}</div>
                <p className="text-sm text-textmut leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </Reveal>
    </section>
  );
}
