import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { Link, MemoryRouter } from 'react-router-dom';
import { ScrollToRoute } from './App';

describe('route scrolling', () => {
  it('opens reports at the top and follows the scan history link', () => {
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
    const scrollIntoView = vi.fn();
    const history = document.createElement('div');
    history.id = 'history';
    history.scrollIntoView = scrollIntoView;
    document.body.append(history);

    render(
      <MemoryRouter initialEntries={['/scan/123']}>
        <ScrollToRoute />
        <Link to="/dashboard#history">History</Link>
      </MemoryRouter>,
    );
    expect(scrollTo).toHaveBeenCalledWith(0, 0);
    fireEvent.click(screen.getByRole('link', { name: 'History' }));
    expect(scrollIntoView).toHaveBeenCalledOnce();

    history.remove();
    scrollTo.mockRestore();
  });
});
