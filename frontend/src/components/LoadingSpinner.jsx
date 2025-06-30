import React from 'react';

const LoadingSpinner = ({ 
  message = "Searching through CV database...",
  size = 'medium',
  fullWidth = false,
  className = ''
}) => {
  const sizeClasses = {
    small: 'h-4 w-4',
    medium: 'h-6 w-6',
    large: 'h-10 w-10'
  };

  const textSizes = {
    small: 'text-sm',
    medium: 'text-base',
    large: 'text-lg'
  };

  const spinner = (
    <div className={`flex items-center justify-center space-x-3 ${className}`}>
      <svg 
        className={`animate-spin ${sizeClasses[size] || sizeClasses.medium} text-[#45B39C]`} 
        xmlns="http://www.w3.org/2000/svg" 
        fill="none" 
        viewBox="0 0 24 24"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      {message && (
        <span className={`${textSizes[size] || textSizes.medium} text-[#4A5A6B]`}>
          {message}
        </span>
      )}
    </div>
  );

  if (fullWidth) {
    return (
      <div className="bg-white/80 rounded-2xl shadow-xl border border-[#4A5A6B]/20 p-8">
        {spinner}
      </div>
    );
  }

  return spinner;
};

export default LoadingSpinner;