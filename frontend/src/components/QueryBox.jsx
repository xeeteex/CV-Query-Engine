import React, { useState } from 'react';

const QueryBox = ({ onAskQuestion, loading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    onAskQuestion(query);
  };

  const exampleQueries = [
    "Find candidates with Python experience",
    "Who has worked at Google?",
    "Show me developers with 5+ years experience",
    "Find candidates with machine learning skills",
     ];

  return (
    <div className="space-y-6">
      {/* Query Form */}
      <div className="bg-white rounded-3xl shadow-xl border border-[#4A5A6B]/20 p-8 mb-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-[#4A5A6B] mb-2">
              What would you like to know about the candidates?
            </label>
            <div className="mt-1 relative">
              <textarea
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Find candidates with Python experience, Who has worked at Google?, Show me developers with 5+ years experience..."
                className="w-full px-4 py-4 border border-[#4A5A6B]/30 rounded-2xl focus:ring-2 focus:ring-[#45B39C] focus:border-transparent resize-none text-[#4A5A6B]"
                rows={3}
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="absolute bottom-4 right-4 bg-[#45B39C] text-white px-5 py-2.5 rounded-xl font-semibold text-sm shadow-md hover:bg-[#3AA98C] focus:ring-2 focus:ring-offset-2 focus:ring-[#45B39C] disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200"
              >
                <div className="flex items-center space-x-2">
                  {loading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>Searching...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                      <span>Search CVs</span>
                    </>
                  )}
                </div>
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Example Queries */}
      <div className="bg-white/80 rounded-3xl p-6 border border-[#4A5A6B]/20">
        <h3 className="text-lg font-semibold text-[#4A5A6B] mb-4">Example Queries</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {exampleQueries.map((example, index) => (
            <button
              key={index}
              onClick={() => setQuery(example)}
              className="text-left p-3 bg-white rounded-xl border border-[#4A5A6B]/20 hover:border-[#45B39C] hover:bg-[#45B39C]/10 transition-all duration-200 text-sm text-[#4A5A6B]"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default QueryBox;
