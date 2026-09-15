import React, { useEffect, useRef, useState } from 'react';

// Landing-page-only fade/reveal on scroll entry. Native IntersectionObserver,
// no animation library. Fires once (unobserves after first intersection) —
// this is a one-time "read once" marketing page, not something a visitor
// re-scrolls through expecting the same beat every time. Honors
// prefers-reduced-motion by skipping straight to visible.
export default function Reveal({ children, className = '', delay = 0 }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // jsdom (this project's own test environment) implements neither API —
    // fail open to visible rather than crash or never reveal, since hiding
    // content forever is worse than skipping the fade-in.
    if (typeof window.matchMedia !== 'function' || typeof window.IntersectionObserver !== 'function') {
      setVisible(true);
      return;
    }
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisible(true);
      return;
    }
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.unobserve(el);
        }
      },
      { threshold: 0.15, rootMargin: '0px 0px -80px 0px' }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`transition-all duration-700 ease-out ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'} ${className}`}
      style={{ transitionDelay: visible ? `${delay}ms` : '0ms' }}
    >
      {children}
    </div>
  );
}
