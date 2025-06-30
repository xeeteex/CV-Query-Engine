import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import LoadingSpinner from './LoadingSpinner';

const ChatContainer = ({ onSendMessage, messages = [], loading = false }) => {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (message) => {
    onSendMessage(message);
  };

  return (
    <div className="flex flex-col h-screen bg-[#E1E6E9]">
      {/* Header */}
      <div className="bg-white/90 border-b border-[#64798A]/20 p-4 shadow-sm">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <div className="flex items-center">
            <h1 className="text-lg font-semibold text-[#64798A]">TriNetra CV Query Engine</h1>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 pb-24">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((msg, index) => (
            <ChatMessage key={index} message={msg.text} isUser={msg.isUser}>
              {msg.content}
            </ChatMessage>
          ))}
          {loading && (
            <div className="flex justify-start mb-4">
              <div className="flex max-w-3xl">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#45B39C] text-white mr-3 flex items-center justify-center">
                  A
                </div>
                <div className="p-4 bg-white/90 rounded-2xl shadow">
                  <LoadingSpinner size="small" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <ChatInput onSendMessage={handleSendMessage} loading={loading} />
    </div>
  );
};

export default ChatContainer;
