import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import ScanDetail from './pages/ScanDetail'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/scan/:id" element={<ScanDetail />} />
      </Routes>
    </Router>
  )
}

export default App
