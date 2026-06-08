import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import NewScan from './pages/NewScan';
import ScanDetail from './pages/ScanDetail';
import FindingDetail from './pages/FindingDetail';
import Intelligence from './pages/Intelligence';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scan/new" element={<NewScan />} />
          <Route path="/scan/:scan_id" element={<ScanDetail />} />
          <Route path="/scan/:scan_id/finding/:finding_id" element={<FindingDetail />} />
          <Route path="/intelligence" element={<Intelligence />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
