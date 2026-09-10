import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

vi.mock('../api/client', () => ({
  default: { get: vi.fn() },
}));

import client from '../api/client';
import ScanComparison from './ScanComparison';

const SCAN_ID = 'scan-2';
const PREV_SCAN_ID = 'scan-1';

const diffResponse = {
  data: {
    scan_id: SCAN_ID,
    compared_to_scan_id: PREV_SCAN_ID,
    target: 'example.com',
    scan_date: '2026-09-11T10:00:00Z',
    compared_scan_date: '2026-09-10T10:00:00Z',
    summary: { new: 1, resolved: 1, changed: 1, unchanged: 2 },
    new_findings: [
      { id: 'f1', type: 'port', title: 'Port 8080/tcp: http', severity: 'medium', final_risk_score: 5.0 },
    ],
    resolved_findings: [
      { id: 'f2', type: 'port', title: 'Port 21/tcp: ftp', severity: 'low', final_risk_score: 2.0 },
    ],
    changed_findings: [
      {
        finding: { id: 'f3', type: 'port', title: 'Port 22/tcp: ssh', severity: 'high', final_risk_score: 7.5 },
        previous_risk_score: 4.0,
        previous_severity: 'medium',
        previous_confidence: 0.8,
      },
    ],
    unchanged_findings: [
      { id: 'f4', type: 'technology', title: 'Live Host: http://example.com', severity: 'low', final_risk_score: 3.0 },
      { id: 'f5', type: 'subdomain', title: 'Subdomain: www.example.com', severity: 'informational', final_risk_score: 2.0 },
    ],
  },
};

const history = [
  { id: SCAN_ID, created_at: '2026-09-11T10:00:00Z', status: 'completed', finding_count: 5 },
  { id: PREV_SCAN_ID, created_at: '2026-09-10T10:00:00Z', status: 'completed', finding_count: 4 },
];

describe('ScanComparison', () => {
  beforeEach(() => {
    client.get.mockReset();
    client.get.mockResolvedValue(diffResponse);
  });

  it('fetches the diff without compare_to on initial load', async () => {
    render(<ScanComparison scanId={SCAN_ID} history={history} />);

    await screen.findByText(/1 new/);

    expect(client.get).toHaveBeenCalledWith(`/scans/${SCAN_ID}/diff`);
  });

  it('renders the summary counts from the mocked diff response', async () => {
    render(<ScanComparison scanId={SCAN_ID} history={history} />);

    await screen.findByText(/1 new/);
    screen.getByText(/1 resolved/);
    screen.getByText(/1 changed/);
    // Anchored to end-of-string: the summary span's text is exactly "2
    // unchanged", while the collapsible toggle's text is "2 unchanged
    // findings" — both would match an unanchored /2 unchanged/.
    screen.getByText(/2 unchanged$/);
  });

  it('shows a NEW badge for new findings and a RESOLVED badge for resolved findings', async () => {
    render(<ScanComparison scanId={SCAN_ID} history={history} />);

    await screen.findByText('Port 8080/tcp: http');
    screen.getByText('NEW');
    screen.getByText('Port 21/tcp: ftp');
    screen.getByText('RESOLVED');
  });

  it('shows the old -> new risk score for changed findings', async () => {
    render(<ScanComparison scanId={SCAN_ID} history={history} />);

    await screen.findByText(/4\.0 → 7\.5/);
  });

  it('keeps unchanged findings collapsed until the toggle is clicked', async () => {
    render(<ScanComparison scanId={SCAN_ID} history={history} />);

    await screen.findByText(/2 unchanged findings/);
    expect(screen.queryByText('Live Host: http://example.com')).toBeNull();

    fireEvent.click(screen.getByText(/2 unchanged findings/));

    await screen.findByText('Live Host: http://example.com');
    screen.getByText('Subdomain: www.example.com');
  });

  it('does not show a picker when only one other scan exists', async () => {
    render(<ScanComparison scanId={SCAN_ID} history={history} />);
    await screen.findByText(/1 new/);
    expect(screen.queryByText(/Compare against/)).toBeNull();
  });

  it('shows a picker and refetches with an explicit compare_to when more than one other scan exists', async () => {
    const thirdScanId = 'scan-0';
    const historyWithThree = [
      ...history,
      { id: thirdScanId, created_at: '2026-09-09T10:00:00Z', status: 'completed', finding_count: 3 },
    ];

    render(<ScanComparison scanId={SCAN_ID} history={historyWithThree} />);
    await screen.findByText(/1 new/);

    const select = screen.getByText(/Compare against/).closest('div').querySelector('select');
    expect(select).not.toBeNull();

    fireEvent.change(select, { target: { value: thirdScanId } });

    expect(client.get).toHaveBeenCalledWith(`/scans/${SCAN_ID}/diff?compare_to=${thirdScanId}`);
  });
});
