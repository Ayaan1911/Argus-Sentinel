import React, { useEffect, useState } from 'react';
import { Search, Server, Code, ShieldAlert, ChevronDown, ChevronUp } from 'lucide-react';
import client from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import SeverityBadge from '../components/SeverityBadge';

const EntryCard = ({ entry, type }) => {
  const [expanded, setExpanded] = useState(false);
  // vulnerabilities/*.json entries use "vulnerability_class" as their name
  // field, not "vulnerability" — without this fallback, half the library's
  // vulnerability entries render with a blank title.
  const name = entry.service || entry.technology || entry.vulnerability_class || entry.vulnerability;
  
  return (
    <div className="bg-card border border-bordercolor rounded-lg overflow-hidden transition-all">
      <div 
        className="p-4 cursor-pointer hover:bg-surface/50 flex justify-between items-start"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h3 className="font-bold text-textpri text-lg">{name}</h3>
            {entry.risk_level && <SeverityBadge severity={entry.risk_level} />}
            {entry.port && <span className="text-xs font-mono bg-surface border border-bordercolor px-2 py-0.5 rounded text-textmut">Port {entry.port}</span>}
          </div>
          <p className={`text-sm text-textmut ${expanded ? '' : 'line-clamp-2'}`}>{entry.description}</p>
        </div>
        <div className="text-textmut mt-1">
          {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </div>
      </div>
      
      {expanded && (
        <div className="p-4 border-t border-bordercolor bg-surface/30 space-y-4">
          {entry.common_risks && (
            <div>
              <div className="text-xs font-bold text-textpri uppercase tracking-wider mb-2">Common Risks</div>
              <ul className="text-sm text-textmut list-disc list-inside space-y-1">
                {entry.common_risks.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}
          {entry.misconfigurations && (
            <div>
              <div className="text-xs font-bold text-textpri uppercase tracking-wider mb-2">Misconfigurations</div>
              <ul className="text-sm text-textmut list-disc list-inside space-y-1">
                {entry.misconfigurations.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}
          {entry.audience_guidance && (
            <div>
              <div className="text-xs font-bold text-textpri uppercase tracking-wider mb-2">Student Guidance</div>
              <p className="text-sm text-textmut whitespace-pre-wrap">{entry.audience_guidance.student}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default function Intelligence() {
  const [data, setData] = useState({ services: {}, technologies: {}, vulnerabilities: {} });
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('services');
  const [search, setSearch] = useState('');
  const [searchResults, setSearchResults] = useState(null);

  useEffect(() => {
    Promise.all([
      client.get('/intelligence/services'),
      client.get('/intelligence/technologies'),
      client.get('/intelligence/vulnerabilities')
    ]).then(([s, t, v]) => {
      setData({
        services: s.data,
        technologies: t.data,
        vulnerabilities: v.data
      });
      setLoading(false);
    }).catch(err => setLoading(false));
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!search.trim()) {
      setSearchResults(null);
      return;
    }
    setLoading(true);
    try {
      const res = await client.get(`/intelligence/search?q=${search}`);
      setSearchResults(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data.services) return <LoadingSpinner />;

  const currentData = searchResults 
    ? searchResults 
    : Object.values(data[tab] || {});

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-textpri">Intelligence Library</h2>
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
            placeholder="Search KB..." 
            className="w-full bg-card border border-bordercolor rounded-md pl-10 pr-4 py-2 text-sm text-textpri focus:outline-none focus:border-accent transition-colors"
          />
          <Search size={16} className="absolute left-3 top-2.5 text-textmut" />
        </form>
      </div>

      {!searchResults && (
        <div className="flex border-b border-bordercolor space-x-6">
          <button 
            onClick={() => setTab('services')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${tab === 'services' ? 'border-accent text-accent' : 'border-transparent text-textmut hover:text-textpri'}`}
          ><Server size={16} /> Services</button>
          <button 
            onClick={() => setTab('technologies')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${tab === 'technologies' ? 'border-accent text-accent' : 'border-transparent text-textmut hover:text-textpri'}`}
          ><Code size={16} /> Technologies</button>
          <button 
            onClick={() => setTab('vulnerabilities')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${tab === 'vulnerabilities' ? 'border-accent text-accent' : 'border-transparent text-textmut hover:text-textpri'}`}
          ><ShieldAlert size={16} /> Vulnerabilities</button>
        </div>
      )}

      {searchResults && (
        <div className="text-sm text-textmut mb-4">
          Found {searchResults.length} results for "{search}"
          <button onClick={() => {setSearch(''); setSearchResults(null);}} className="ml-4 text-accent hover:underline">Clear Search</button>
        </div>
      )}

      <div className="space-y-4">
        {searchResults ? (
          searchResults.map((item, i) => (
            <EntryCard key={i} entry={item.entry} type={item.type} />
          ))
        ) : (
          currentData.map((item, i) => (
            <EntryCard key={i} entry={item} type={tab} />
          ))
        )}
        
        {currentData.length === 0 && (
          <div className="text-center p-12 text-textmut bg-card border border-bordercolor rounded-lg">
            No entries found.
          </div>
        )}
      </div>
    </div>
  );
}
