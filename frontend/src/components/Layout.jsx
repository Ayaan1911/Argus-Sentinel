import React from 'react';
import EditorialNav from './EditorialNav';
import '../editorial.css';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export default function Layout({ children }) {
  return (
    <div className="editorial editorial-workspace">
      <EditorialNav workspace />
      {DEMO_MODE && (
        <div className="editorial-demo">
          Public demo · scans are limited to the bundled Juice Shop target.{' '}
          <a href="https://github.com/Ayaan1911/Argus-Sentinel#readme" target="_blank" rel="noreferrer">Self-host to scan your own targets ↗</a>
        </div>
      )}
      <main className="editorial-wrap editorial-page">{children}</main>
    </div>
  );
}
