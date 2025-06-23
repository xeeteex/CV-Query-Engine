// src/App.jsx
import React, { useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import './App.css';

// Import components
import Header from './components/Header';
import Hero from './components/Hero';
import QueryBox from './components/QueryBox';
import AnswerCard from './components/AnswerCard';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorMessage from './components/ErrorMessage';
import Login from './components/auth/Login';
import Register from './components/auth/Register';

// Import API service
import { cvApi } from './api/cvApi';

const AppContent = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [structuredData, setStructuredData] = useState([]);
  const { isAuthenticated, logout } = useAuth();
  const location = useLocation();

  const handleAskQuestion = async (question) => {
    setLoading(true);
    setError(null);
    setAnswer('');
    setSources([]);
    setStructuredData([]);

    try {
      const response = await cvApi.askQuestion(question);
      
      if (response.error) {
        setError(response.error);
      } else {
        setAnswer(response.answer);
        setSources(response.sources || []);
        setStructuredData(response.structured_data || []);
      }
    } catch (err) {
      setError(err.message || 'Failed to get answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // If user is not authenticated and not on auth pages, redirect to login
  if (!isAuthenticated && !['/login', '/register'].includes(location.pathname)) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <div className="min-h-screen bg-[#E1E6E9] overflow-hidden">
      <div className="bg-white/90 max-w-7xl mx-auto min-h-screen">
        {isAuthenticated && <Header onLogout={logout} />}
        
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/login" element={
              <div className="pt-16">
                <Login onLogin={() => window.location.href = '/'} />
              </div>
            } />
            <Route path="/register" element={
              <div className="pt-16">
                <Register onRegister={() => window.location.href = '/login'} />
              </div>
            } />
            <Route path="/" element={
              <>
                <Hero />
                <QueryBox onAskQuestion={handleAskQuestion} loading={loading} />
                {loading && <LoadingSpinner />}
                {error && <ErrorMessage error={error} />}
                {!loading && answer && (
                  <AnswerCard 
                    answer={answer} 
                    sources={sources} 
                    structuredData={structuredData} 
                  />
                )}
              </>
            } />
          </Routes>
        </main>
      </div>
    </div>
  );
};

const App = () => {
  return <AppContent />;
};

export default App;