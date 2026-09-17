import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';

// Pages
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import StudyAssistant from './pages/StudyAssistant';
import ConversationsList from './pages/ConversationsList';
import ConversationView from './pages/ConversationView';
import StudyMaterials from './pages/StudyMaterials';
import DocumentDetail from './pages/DocumentDetail';
import LearningResources from './pages/LearningResources';
import SavedResources from './pages/SavedResources';
import Profile from './pages/Profile';

export default function App() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar />
      <main style={{ flex: 1 }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/study" element={<StudyAssistant />} />
          <Route path="/assistant" element={<Navigate to="/study" replace />} />
          <Route path="/chat/:id" element={<ConversationView />} />
          <Route path="/conversations" element={<ConversationsList />} />
          <Route path="/materials" element={<StudyMaterials />} />
          <Route path="/materials/:id" element={<DocumentDetail />} />
          <Route path="/resources" element={<LearningResources />} />
          <Route path="/saved" element={<SavedResources />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/settings" element={<Navigate to="/profile" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
