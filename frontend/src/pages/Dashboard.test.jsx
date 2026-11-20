import React from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('../api/client', () => ({ default: { get: vi.fn() } }));

import client from '../api/client';
import Dashboard from './Dashboard';

afterEach(() => vi.clearAllMocks());

function renderDashboard() {
  return render(<MemoryRouter><Dashboard /></MemoryRouter>);
}

describe('editorial dashboard', () => {
  it('separates the latest scan from cumulative records and shows its real comparison', async () => {
    const scans = [
      { id: 'new', target: 'juice-shop', status: 'completed', finding_count: 3, created_at: '2026-11-21T00:00:00Z' },
      { id: 'old', target: 'juice-shop', status: 'completed', finding_count: 15, created_at: '2026-11-20T00:00:00Z' },
    ];
    client.get.mockImplementation(path => {
      if (path === '/scans/?limit=50') return Promise.resolve({ data: scans });
      if (path === '/scans/dashboard-stats') return Promise.resolve({ data: { total_scans: 2, total_findings: 18 } });
      if (path === '/findings/scan/new/summary') return Promise.resolve({ data: {
        by_severity: { critical: 0, high: 0, medium: 0, low: 1, informational: 2 },
        top_findings: [{ id: 'finding-1', title: 'Port 3000/tcp', final_risk_score: 3.0 }],
      } });
      if (path === '/scans/new/diff') return Promise.resolve({ data: { summary: { new: 1, resolved: 13 } } });
      throw new Error('Unexpected request: ' + path);
    });

    renderDashboard();
    await waitFor(() => expect(screen.getByText('New since prior scan')).not.toBeNull());
    expect(screen.getByText('Findings in this scan').parentElement.textContent).toContain('3');
    expect(screen.getByText('New since prior scan').parentElement.textContent).toContain('1');
    expect(screen.getByText('No longer found').parentElement.textContent).toContain('13');
    expect(screen.getByText(/Historical totals:/).textContent).toContain('18 finding records');
    expect(screen.getByRole('link', { name: /Port 3000\/tcp/i }).getAttribute('href')).toBe('/scan/new/finding/finding-1');
  });

  it('explains when a first scan has no comparison', async () => {
    client.get.mockImplementation(path => {
      if (path === '/scans/?limit=50') return Promise.resolve({ data: [
        { id: 'first', target: 'juice-shop', status: 'completed', finding_count: 0, created_at: '2026-11-21T00:00:00Z' },
      ] });
      if (path === '/scans/dashboard-stats') return Promise.resolve({ data: { total_scans: 1, total_findings: 0 } });
      if (path === '/findings/scan/first/summary') return Promise.resolve({ data: { by_severity: {}, top_findings: [] } });
      if (path === '/scans/first/diff') return Promise.reject({ response: { status: 404 } });
      throw new Error('Unexpected request: ' + path);
    });

    renderDashboard();
    expect(await screen.findByText(/No earlier completed scan of this target/)).not.toBeNull();
    expect(screen.getByText('Findings in this scan').parentElement.textContent).toContain('0');
  });
});
