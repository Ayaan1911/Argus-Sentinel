import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { GITHUB_URL } from '../pages/landing/data';

export default function EditorialNav({ workspace = false }) {
  const { pathname } = useLocation();
  return (
    <header className="editorial-nav">
      <div className="editorial-wrap editorial-nav-inner">
        <Link className="editorial-brand" to="/" aria-label="Argus Sentinel home">
          <span className="editorial-mark" aria-hidden="true">A</span>
          <span>ARGUS SENTINEL</span>
        </Link>
        <nav className="editorial-nav-links" aria-label="Main navigation">
          {workspace ? (
            <>
              <Link to="/dashboard" aria-current={pathname === '/dashboard' ? 'page' : undefined}>Overview</Link>
              <Link to="/dashboard#history">Scan history</Link>
              <Link to="/intelligence" aria-current={pathname === '/intelligence' ? 'page' : undefined}>Intelligence</Link>
            </>
          ) : (
            <>
              <a href="#method">The method</a>
              <a href="#evidence">Evidence</a>
              <a href={GITHUB_URL} target="_blank" rel="noreferrer">Open source</a>
            </>
          )}
        </nav>
        <Link className="editorial-button editorial-nav-cta" to={workspace ? '/scan/new' : '/dashboard'} aria-current={workspace && pathname === '/scan/new' ? 'page' : undefined}>
          {workspace ? 'Start a scan' : 'Open Argus'} <span aria-hidden="true">↗</span>
        </Link>
      </div>
    </header>
  );
}
