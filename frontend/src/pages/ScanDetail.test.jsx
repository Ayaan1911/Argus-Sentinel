import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

vi.mock('../api/client', () => ({
  default: { get: vi.fn() },
}));

import client from '../api/client';
import ScanDetail, { nextPollDelay } from './ScanDetail';

const SCAN_ID = 'test-scan-id';

function statusResponse(status) {
  return {
    data: {
      scan_id: SCAN_ID,
      target: 'example.com',
      audience: 'pentester',
      status,
      stage_status: {},
      finding_count: 0,
    },
  };
}

const summaryResponse = {
  data: {
    scan_id: SCAN_ID,
    target: 'example.com',
    total_findings: 0,
    by_severity: { critical: 0, high: 0, medium: 0, low: 0, informational: 0 },
    by_type: {},
    top_findings: [],
    combined_risk_level: 'informational',
    audience: 'pentester',
  },
};

const emptyFindingsResponse = { data: [] };

function renderScanDetail() {
  return render(
    <MemoryRouter initialEntries={[`/scan/${SCAN_ID}`]}>
      <Routes>
        <Route path="/scan/:scan_id" element={<ScanDetail />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('nextPollDelay (backoff schedule)', () => {
  it('polls every 3s for the first 30s', () => {
    expect(nextPollDelay(0)).toBe(3000);
    expect(nextPollDelay(15000)).toBe(3000);
    expect(nextPollDelay(29999)).toBe(3000);
  });

  it('polls every 5s from 30s up to 2 minutes', () => {
    expect(nextPollDelay(30000)).toBe(5000);
    expect(nextPollDelay(60000)).toBe(5000);
    expect(nextPollDelay(119999)).toBe(5000);
  });

  it('polls every 10s after 2 minutes', () => {
    expect(nextPollDelay(120000)).toBe(10000);
    expect(nextPollDelay(600000)).toBe(10000);
  });
});

describe('ScanDetail polling', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    client.get.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('polls the lightweight status endpoint repeatedly while running, then stops and fetches full data exactly once on reaching a terminal state', async () => {
    let statusCallCount = 0;
    client.get.mockImplementation((url) => {
      if (url.includes('/status')) {
        statusCallCount += 1;
        // Stay "running" for the first two polls, then complete.
        const status = statusCallCount < 3 ? 'running' : 'completed';
        return Promise.resolve(statusResponse(status));
      }
      if (url.includes('/summary')) {
        return Promise.resolve(summaryResponse);
      }
      return Promise.resolve(emptyFindingsResponse);
    });

    renderScanDetail();

    // Initial poll fires immediately on mount.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(statusCallCount).toBe(1);
    expect(screen.queryByText(/scan not found/i)).toBeNull();

    // t=3000: second poll (still within the first-30s / 3s-cadence window).
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });
    expect(statusCallCount).toBe(2);

    // t=6000: third poll — this is the one that reports "completed".
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });
    expect(statusCallCount).toBe(3);

    // Full findings payload (summary + findings list) is fetched exactly once,
    // triggered by the terminal transition.
    const summaryCalls = client.get.mock.calls.filter(([url]) => url.includes('/summary'));
    const findingsCalls = client.get.mock.calls.filter(
      ([url]) => url.includes(`/findings/scan/${SCAN_ID}`) && !url.includes('/summary')
    );
    expect(summaryCalls.length).toBe(1);
    expect(findingsCalls.length).toBe(1);

    // Advancing well past any backoff interval must NOT produce further status
    // polls — polling stops entirely once a terminal state is reached.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(60000);
    });
    expect(statusCallCount).toBe(3);
  });

  it('fetches the full findings payload immediately when the scan is already terminal on first load', async () => {
    client.get.mockImplementation((url) => {
      if (url.includes('/status')) {
        return Promise.resolve(statusResponse('completed'));
      }
      if (url.includes('/summary')) {
        return Promise.resolve(summaryResponse);
      }
      return Promise.resolve(emptyFindingsResponse);
    });

    renderScanDetail();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    const statusCalls = client.get.mock.calls.filter(([url]) => url.includes('/status'));
    const summaryCalls = client.get.mock.calls.filter(([url]) => url.includes('/summary'));
    expect(statusCalls.length).toBe(1);
    expect(summaryCalls.length).toBe(1);

    // No further polling should ever occur for an already-terminal scan.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(30000);
    });
    expect(client.get.mock.calls.filter(([url]) => url.includes('/status')).length).toBe(1);
  });
});
