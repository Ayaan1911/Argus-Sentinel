import React from 'react';
import Nav from './landing/Nav';
import Hero from './landing/Hero';
import Pipeline from './landing/Pipeline';
import Differentiators from './landing/Differentiators';
import Privacy from './landing/Privacy';
import IntelligenceCallout from './landing/IntelligenceCallout';
import Footer from './landing/Footer';

// Standalone marketing page — read once, not part of the app someone uses
// repeatedly. Deliberately does NOT render inside <Layout> (no sidebar, no
// scan chrome): it has its own minimal <Nav>. See App.jsx for the routing
// split and notes.md for why this stays structurally separate from the
// dashboard rather than sharing a shell with it.
export default function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <Nav />
      <Hero />
      <Pipeline />
      <Differentiators />
      <Privacy />
      <IntelligenceCallout />
      <Footer />
    </div>
  );
}
