// src/App.jsx
import React, { useState } from 'react';
import './App.css';

// Import components
import Header from './components/Header';
import Hero from './components/Hero';
import QueryBox from './components/QueryBox';
import AnswerCard from './components/AnswerCard';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorMessage from './components/ErrorMessage';

// Import API service
import { cvApi } from './api/cvApi';

function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [structuredData, setStructuredData] = useState([]);

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

  return (
    
      <div className="bg-white/90 max-w-7xl mx-auto rounded-3xl shadow-md">
        <Header />
        
        <main className="container mx-auto px-4 py-8">
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
        </main>
      </div>
   
  );
}

export default App;