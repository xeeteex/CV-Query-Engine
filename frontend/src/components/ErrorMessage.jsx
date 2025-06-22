import React from 'react';

const ErrorMessage = ({ error }) => {
  if (!error) return null;

  return (
    <div className="bg-red-50/80 border border-red-200 rounded-2xl p-6 shadow-sm">
      <div className="flex items-start space-x-3">
        <svg className="w-6 h-6 text-red-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
          <h3 className="text-lg font-medium text-red-800">Error</h3>
          <p className="text-red-700 mt-1">{error}</p>
        </div>
      </div>
    </div>
  );
};

export default ErrorMessage;