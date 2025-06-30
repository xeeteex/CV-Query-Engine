import React from 'react';

const ChatMessage = ({ message, isUser = false, children}) => {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-3xl ${isUser ? 'flex-row-reverse' : ''}`}>
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${isUser ? 'bg-[#45B39C] text-white ml-3' : 'bg-[#45B39C] text-white mr-3'}`}>
          {isUser ? 'U' : 'A'}
        </div>
        <div className={`p-4 rounded-2xl shadow ${isUser ? 'bg-[#45B39C] text-white' : 'bg-white/90 text-[#64798A]'}`}>
          {children || message}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
