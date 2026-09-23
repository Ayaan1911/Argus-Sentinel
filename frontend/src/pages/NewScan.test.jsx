import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('../api/client', () => ({
  default: { post: vi.fn(() => Promise.resolve({ data: { id: 'scan-123' } })) },
}));

import client from '../api/client';

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

// NewScan.jsx reads VITE_DEMO_MODE into a module-level constant at import
// time, so each mode has to be exercised via a fresh dynamic import after
// stubbing the env var, not a single static import shared across tests.
async function renderNewScan() {
  const { default: NewScan } = await import('./NewScan');
  return render(
    <MemoryRouter>
      <NewScan />
    </MemoryRouter>
  );
}

describe('NewScan in demo mode', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_DEMO_MODE', 'true');
  });

  it('offers a locked choice between the two authorized demo targets, no free-text input', async () => {
    await renderNewScan();

    expect(screen.getByRole('tab', { name: /juice-shop/i })).not.toBeNull();
    expect(screen.getByRole('tab', { name: /scanme\.nmap\.org/i })).not.toBeNull();
    expect(screen.queryByPlaceholderText(/example\.com/i)).toBeNull();
  });

  it('defaults to juice-shop and submits whichever demo target is selected', async () => {
    await renderNewScan();

    fireEvent.click(screen.getByRole('tab', { name: /scanme\.nmap\.org/i }));
    fireEvent.click(screen.getByRole('button', { name: /run demo scan/i }));

    await waitFor(() => {
      expect(client.post).toHaveBeenCalledWith('/scans/', { target: 'scanme.nmap.org', audience: 'student' });
    });
  });
});

describe('NewScan in self-hosted (non-demo) mode', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_DEMO_MODE', 'false');
  });

  it('renders a free-text target input, not the locked demo selector', async () => {
    await renderNewScan();

    expect(screen.getByPlaceholderText(/example\.com/i)).not.toBeNull();
    // AudienceSelector also uses role="tab", so scope this to the demo
    // target tablist specifically rather than asserting no tabs at all.
    expect(screen.queryByRole('tablist', { name: /demo target/i })).toBeNull();
  });

  it('picking a persona does not submit the form', async () => {
    client.post.mockClear();
    await renderNewScan();

    fireEvent.change(screen.getByPlaceholderText(/example\.com/i), { target: { value: 'juice-shop' } });
    fireEvent.click(screen.getByRole('tab', { name: /pentester/i }));

    expect(client.post).not.toHaveBeenCalled();
  });
});
