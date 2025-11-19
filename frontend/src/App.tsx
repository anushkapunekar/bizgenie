import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import BusinessRegister from './pages/BusinessRegister';
import BusinessDashboard from './pages/BusinessDashboard';
import Chat from './pages/Chat';
import BusinessLogin from './pages/BusinessLogin';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/register" element={<BusinessRegister />} />
          <Route path="/login" element={<BusinessLogin />} />
          <Route path="/business/:id" element={<BusinessDashboard />} />
          <Route path="/business/:id/chat" element={<Chat />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;

