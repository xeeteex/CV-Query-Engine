// src/App.jsx
import React, { useState, useCallback } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import './App.css';

// Import components
import Header from './components/Header';
import ChatContainer from './components/ChatContainer';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import LoadingSpinner from './components/LoadingSpinner';

// Import API service
import { cvApi } from './api/cvApi';

const AppContent = () => {
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: 'Hello! I can help you find information from CVs. What would you like to know?',
      isUser: false,
      timestamp: new Date()
    }
  ]);
  const { isAuthenticated, loading: authLoading, logout } = useAuth();
  const location = useLocation();

  // Show loading state while checking authentication
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  const handleSendMessage = useCallback(async (message, response = null, candidates = null) => {
    // Add user message to chat
    const userMessage = {
      id: Date.now(),
      text: message,
      isUser: true,
      timestamp: new Date(),
      content: message
    };

    setMessages(prev => [...prev, userMessage]);
    
    // If response is already provided (from ChatContainer), use it
    if (response !== null) {
      const botMessage = {
        id: Date.now() + 1,
        text: response,
        isUser: false,
        timestamp: new Date(),
        content: response,
        candidates: candidates
      };
      setMessages(prev => [...prev, botMessage]);
      return;
    }
    
    // Fallback to old API if needed (for backward compatibility)
    setLoading(true);

    try {
      // Simulate API call
      const response = await cvApi.askQuestion(message);
      
      if (response.error) {
        throw new Error(response.error);
      }

      // Add assistant's response to chat
      const assistantMessage = {
        id: Date.now() + 1,
        text: response.answer,
        isUser: false,
        timestamp: new Date(),
        content: response.answer // For rich content
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again.',
        isUser: false,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }, [cvApi]);

  // If user is not authenticated and not on auth pages, redirect to login
  if (!isAuthenticated && !['/login', '/register'].includes(location.pathname)) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/login" element={
          <div className="min-h-screen flex flex-col">
            <Header />
            <div className="flex-1 flex items-center justify-center px-4">
              <Login />
            </div>
          </div>
        } />
        <Route path="/register" element={
          <div className="min-h-screen flex flex-col">
            <Header />
            <div className="flex-1 flex items-center justify-center px-4">
              <Register />
            </div>
          </div>
        } />
        <Route path="/" element={
          <div className="flex flex-col h-screen">
            <Header onLogout={logout} />
            <ChatContainer 
              messages={messages} 
              onSendMessage={handleSendMessage} 
              isLoading={loading}
            />
          </div>
        } />
      </Routes>
    </div>
  );
};

const App = () => {
  return <AppContent />;
};

export default App;