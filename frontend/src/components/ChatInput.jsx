import React, { useState } from 'react';

const ChatInput = ({ onSendMessage, loading }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!message.trim() || loading) return;
    onSendMessage(message);
    setMessage('');
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white/90 border-t border-[#64798A]/20 p-4 shadow-lg">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="relative">
          <div className="flex items-center">
            <button
              type="button"
              className="p-2 hover:text-[#45B39C] transition-colors mr-2"
              title="Attach files"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
            <div className="flex-1 relative">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Reply to TriNetra..."
                className="w-full px-4 py-3 pr-12 border border-[#64798A]/30 rounded-full focus:outline-none focus:ring-2 focus:ring-[#45B39C] focus:border-transparent text-[#64798A] placeholder-[#64798A]/60"
                disabled={loading}
              />
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center">
                <button
                  type="submit"
                  className={`p-1.5 rounded-full ${!message.trim() || loading ? 'text-[#64798A]/30' : 'text-[#45B39C] hover:bg-[#45B39C]/10'}`}
                  disabled={!message.trim() || loading}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatInput;
