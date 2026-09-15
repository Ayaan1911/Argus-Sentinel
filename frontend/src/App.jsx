import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import NewScan from './pages/NewScan';
import ScanDetail from './pages/ScanDetail';
import FindingDetail from './pages/FindingDetail';
import Intelligence from './pages/Intelligence';

// "/" is the standalone landing page (no sidebar/header chrome — see
// Landing.jsx). Everything that used to live at "/" moved to "/dashboard";
// every other app route is unchanged, each still wrapped in <Layout>
// individually rather than via a nested route, matching how this file
// already worked before the landing page existed.
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
        <Route path="/scan/new" element={<Layout><NewScan /></Layout>} />
        <Route path="/scan/:scan_id" element={<Layout><ScanDetail /></Layout>} />
        <Route path="/scan/:scan_id/finding/:finding_id" element={<Layout><FindingDetail /></Layout>} />
        <Route path="/intelligence" element={<Layout><Intelligence /></Layout>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
