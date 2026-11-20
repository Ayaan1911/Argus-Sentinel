import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import NewScan from './pages/NewScan';
import ScanDetail from './pages/ScanDetail';
import FindingDetail from './pages/FindingDetail';
import Intelligence from './pages/Intelligence';

// The landing and overview share the editorial shell. Investigation routes
// retain the existing dense workspace until they receive the same treatment.
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/scan/new" element={<Layout><NewScan /></Layout>} />
        <Route path="/scan/:scan_id" element={<Layout><ScanDetail /></Layout>} />
        <Route path="/scan/:scan_id/finding/:finding_id" element={<Layout><FindingDetail /></Layout>} />
        <Route path="/intelligence" element={<Layout><Intelligence /></Layout>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
