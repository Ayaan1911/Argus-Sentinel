import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ReasoningBreakdown from './ReasoningBreakdown';

// engines/reasoning.py always seeds reasoning_breakdown with a "Base Score"
// entry before appending real modifiers, so the footer must sum only the
// rows after it. Summing the whole array yields the final score, which is a
// different number wearing the "Total Modifier" label.
const BASE = {
  label: 'Base Score',
  modifier: 3.0,
  reason: 'Initial base score derived from finding type and intelligence data.',
};

describe('ReasoningBreakdown', () => {
  it('excludes the base score from the total modifier', () => {
    render(<ReasoningBreakdown breakdown={[BASE, { label: 'Exposed to internet', modifier: 2.0, reason: 'r' }]} />);

    // 2.0, not 5.0 — the base is shown separately, above.
    expect(screen.getByText('+2.0')).toBeTruthy();
    expect(screen.queryByText('+5.0')).toBeNull();
  });

  it('reports a zero total when the breakdown is base-only', () => {
    render(<ReasoningBreakdown breakdown={[BASE]} />);

    expect(screen.getByText('0.0')).toBeTruthy();
    expect(screen.getByText(/left the base score unchanged/)).toBeTruthy();
  });

  it('sums negative modifiers as a net reduction', () => {
    render(<ReasoningBreakdown breakdown={[BASE, { label: 'Patched', modifier: -1.5, reason: 'r' }]} />);

    expect(screen.getByText('−1.5')).toBeTruthy();
    expect(screen.getByText(/lowered this score below its base/)).toBeTruthy();
  });

  it('treats every row as a modifier when no base row is present', () => {
    render(<ReasoningBreakdown breakdown={[{ label: 'Exposed', modifier: 2.5, reason: 'r' }]} />);

    expect(screen.getByText('+2.5')).toBeTruthy();
  });

  it('renders nothing for an empty breakdown', () => {
    const { container } = render(<ReasoningBreakdown breakdown={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
