import React, { useEffect, useMemo, useState } from 'react';
import { Search, Server, Code, ShieldAlert, ExternalLink, Tag } from 'lucide-react';
import client from '../api/client';
import SeverityBadge from '../components/SeverityBadge';
import AudienceSelector from '../components/AudienceSelector';

const TABS = [
  { id: 'services', label: 'Services', Icon: Server },
  { id: 'technologies', label: 'Technologies', Icon: Code },
  { id: 'vulnerabilities', label: 'Vulnerabilities', Icon: ShieldAlert },
];

// vulnerabilities/*.json entries use "vulnerability_class" as their name
// field, not "vulnerability" — without this fallback, half the library's
// vulnerability entries render with a blank title.
function entryName(entry) {
  return entry.service || entry.technology || entry.vulnerability_class || entry.vulnerability || 'Untitled entry';
}

function IntelligenceSkeleton() {
  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-pulse">
      <div className="h-8 w-64 bg-surface rounded" />
      <div className="h-10 w-full bg-surface rounded-lg" />
      <div className="flex gap-6">
        <div className="w-full md:w-1/3 space-y-2">
          {[...Array(6)].map((_, i) => <div key={i} className="h-16 bg-surface rounded-lg" />)}
        </div>
        <div className="hidden md:block w-2/3 h-96 bg-surface rounded-lg" />
      </div>
    </div>
  );
}

function DetailSection({ title, children }) {
  if (!children) return null;
  return (
    <div>
      <div className="text-xs font-bold text-textmut uppercase tracking-wider mb-2">{title}</div>
      {children}
    </div>
  );
}

function DetailList({ items }) {
  if (!items || items.length === 0) return null;
  return (
    <ul className="space-y-1.5">
      {items.map((r, i) => (
        <li key={i} className="text-sm text-textpri flex gap-2">
          <span className="text-accent shrink-0">▹</span> {r}
        </li>
      ))}
    </ul>
  );
}

function EntryDetail({ entry, resultType }) {
  const [audience, setAudience] = useState('student');
  const name = entryName(entry);
  const guidanceKeys = entry.audience_guidance ? Object.keys(entry.audience_guidance) : [];
  const activeAudience = guidanceKeys.includes(audience) ? audience : guidanceKeys[0];

  return (
    <div className="space-y-6">
      <div className="pb-5 border-b border-bordercolor space-y-3">
        <div className="flex items-center gap-2 flex-wrap">
          {resultType && (
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-textmut border border-bordercolor rounded px-1.5 py-0.5">{resultType}</span>
          )}
          {entry.risk_level && <SeverityBadge severity={entry.risk_level} />}
          {entry.severity && <SeverityBadge severity={entry.severity} />}
          {typeof entry.port === 'number' && entry.port > 0 && (
            <span className="text-xs font-mono bg-surface border border-bordercolor px-2 py-0.5 rounded text-textmut">Port {entry.port}{entry.protocol ? `/${entry.protocol}` : ''}</span>
          )}
          {entry.min_secure_version && (
            <span className="text-xs font-mono bg-surface border border-bordercolor px-2 py-0.5 rounded text-textmut">Secure from v{entry.min_secure_version}</span>
          )}
        </div>
        <h2 className="text-3xl font-black text-textpri tracking-tighter leading-tight">{name}</h2>
        <p className="text-textmut text-sm leading-relaxed">{entry.description}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <DetailSection title="Common Risks"><DetailList items={entry.common_risks} /></DetailSection>
        <DetailSection title="Misconfigurations"><DetailList items={entry.misconfigurations} /></DetailSection>
        <DetailSection title="Attack Patterns"><DetailList items={entry.attack_patterns} /></DetailSection>
        <DetailSection title="Recommended Actions"><DetailList items={entry.recommended_actions} /></DetailSection>
      </div>

      <DetailSection title="Real-World Incidents"><DetailList items={entry.real_world_incidents} /></DetailSection>

      {(entry.nuclei_tags?.length > 0 || entry.title_keywords?.length > 0) && (
        <DetailSection title="Matching Signals">
          <div className="flex flex-wrap gap-2">
            {entry.nuclei_tags?.map((t, i) => (
              <span key={`t-${i}`} className="inline-flex items-center gap-1 text-xs font-mono bg-surface border border-bordercolor px-2 py-1 rounded text-textmut"><Tag size={10} /> {t}</span>
            ))}
            {entry.title_keywords?.map((t, i) => (
              <span key={`k-${i}`} className="inline-flex items-center gap-1 text-xs font-mono bg-surface border border-bordercolor px-2 py-1 rounded text-textmut italic">"{t}"</span>
            ))}
          </div>
        </DetailSection>
      )}

      {guidanceKeys.length > 0 && (
        <div className="bg-surface border border-bordercolor rounded-lg overflow-hidden">
          <div className="bg-background/50 px-4 py-3 border-b border-bordercolor">
            <AudienceSelector selected={activeAudience} onChange={setAudience} />
          </div>
          <div className="p-4 text-sm text-textpri leading-relaxed whitespace-pre-wrap">
            {entry.audience_guidance[activeAudience]}
          </div>
        </div>
      )}

      {entry.mitre_attack?.length > 0 && (
        <DetailSection title="MITRE ATT&CK">
          <div className="flex flex-wrap gap-2">
            {entry.mitre_attack.map((t, i) => (
              <span key={i} className="text-xs font-mono bg-surface border border-bordercolor px-2 py-1 rounded text-textmut">{t}</span>
            ))}
          </div>
        </DetailSection>
      )}

      {entry.learning_resources?.length > 0 && (
        <DetailSection title="Learning Resources">
          <ul className="space-y-1.5">
            {entry.learning_resources.map((res, i) => (
              <li key={i}>
                <a href={res} target="_blank" rel="noreferrer" className="text-sm text-accent hover:underline inline-flex items-center gap-1.5">
                  <ExternalLink size={12} /> {res}
                </a>
              </li>
            ))}
          </ul>
        </DetailSection>
      )}
    </div>
  );
}

function ListRow({ entry, resultType, selected, onClick }) {
  const name = entryName(entry);
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-3 rounded-lg border transition-colors ${
        selected ? 'bg-surface border-accent/50' : 'bg-card border-bordercolor hover:bg-surface/50'
      }`}
    >
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="font-semibold text-textpri text-sm truncate">{name}</span>
        {(entry.risk_level || entry.severity) && <SeverityBadge severity={entry.risk_level || entry.severity} />}
      </div>
      <p className="text-xs text-textmut line-clamp-1">{entry.description}</p>
      {resultType && <span className="text-[10px] font-mono uppercase tracking-wider text-textmut/70">{resultType}</span>}
    </button>
  );
}

export default function Intelligence() {
  const [data, setData] = useState({ services: null, technologies: null, vulnerabilities: null });
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('services');
  const [search, setSearch] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [selectedKey, setSelectedKey] = useState(null);

  useEffect(() => {
    Promise.all([
      client.get('/intelligence/services'),
      client.get('/intelligence/technologies'),
      client.get('/intelligence/vulnerabilities'),
    ]).then(([s, t, v]) => {
      setData({ services: s.data, technologies: t.data, vulnerabilities: v.data });
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!search.trim()) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    try {
      const res = await client.get(`/intelligence/search?q=${encodeURIComponent(search)}`);
      setSearchResults(res.data);
      setSelectedKey(0);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const currentList = useMemo(() => {
    if (searchResults) {
      return searchResults.map((r, i) => ({ key: i, entry: r.entry, resultType: r.type }));
    }
    const items = data[tab] || {};
    return Object.entries(items).map(([key, entry]) => ({ key, entry, resultType: null }));
  }, [searchResults, data, tab]);

  useEffect(() => {
    // Keep a valid selection whenever the visible list changes (tab switch,
    // new search results, or the initial load).
    if (currentList.length === 0) {
      setSelectedKey(null);
    } else if (!currentList.some(item => item.key === selectedKey)) {
      setSelectedKey(currentList[0].key);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentList]);

  if (loading) return <IntelligenceSkeleton />;

  const selected = currentList.find(item => item.key === selectedKey);

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-4xl sm:text-5xl font-black text-textpri tracking-tighter leading-none">Intelligence Library</h2>
          <p className="text-textmut text-sm mt-1">The core knowledge base powering Argus Sentinel's deterministic reasoning.</p>
        </div>

        <form onSubmit={handleSearch} className="relative w-full md:w-72">
          <input
            type="text"
            value={search}
            onChange={e => {
              setSearch(e.target.value);
              if (!e.target.value) setSearchResults(null);
            }}
            placeholder="Search the knowledge base..."
            className="w-full bg-card border border-bordercolor rounded-md pl-10 pr-4 py-2 text-sm text-textpri focus:outline-none focus:border-accent transition-colors"
          />
          <Search size={16} className="absolute left-3 top-2.5 text-textmut" />
        </form>
      </div>

      {!searchResults && (
        <div className="flex border-b border-bordercolor space-x-6">
          {TABS.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
                tab === id ? 'border-accent text-accent' : 'border-transparent text-textmut hover:text-textpri'
              }`}
            >
              <Icon size={16} /> {label}
              <span className="text-xs font-mono text-textmut/70">{Object.keys(data[id] || {}).length}</span>
            </button>
          ))}
        </div>
      )}

      {searchResults && (
        <div className="text-sm text-textmut">
          Found {searchResults.length} result{searchResults.length === 1 ? '' : 's'} for "{search}"
          <button onClick={() => { setSearch(''); setSearchResults(null); }} className="ml-4 text-accent hover:underline">Clear search</button>
        </div>
      )}

      {currentList.length === 0 ? (
        <div className="text-center p-12 text-textmut bg-card border border-bordercolor rounded-lg">
          {searching ? 'Searching…' : 'No entries found.'}
        </div>
      ) : (
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="w-full lg:w-1/3 flex flex-col gap-2 max-h-[70vh] overflow-y-auto pr-1">
            {currentList.map(item => (
              <ListRow
                key={item.key}
                entry={item.entry}
                resultType={item.resultType}
                selected={selectedKey === item.key}
                onClick={() => setSelectedKey(item.key)}
              />
            ))}
          </div>

          {selected && (
            <div className="w-full lg:w-2/3 glass rounded-xl p-6 max-h-[70vh] overflow-y-auto">
              <EntryDetail entry={selected.entry} resultType={selected.resultType} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
