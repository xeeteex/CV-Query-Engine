import React, { useState } from 'react';

const AnswerCard = ({ answer, sources, structured_data }) => {
  const [expandedSources, setExpandedSources] = useState(false);
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'compare'
  
  if (!answer) return null;

  // Function to render structured CV data
  const renderStructuredCV = (cvData, index = null, isCompact = false) => {
    if (isCompact) {
      return (
        <div className="space-y-4">
          {/* Compact Header */}
          <div className="text-center border-b border-[#4A5A6B]/20 pb-6">
            <h3 className="text-xl font-bold text-[#4A5A6B] mb-2">{cvData.NAME || 'Unknown'}</h3>
            {cvData.LOCATION && (
              <p className="text-[#4A5A6B]/80 text-sm">{cvData.LOCATION}</p>
            )}
          </div>

          {/* Compact Education */}
          {cvData.EDUCATION && cvData.EDUCATION.length > 0 && (
            <div>
              <h4 className="font-semibold text-[#4A5A6B] mb-2 flex items-center space-x-2">
                <svg className="w-4 h-4 text-[#45B39C]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
                </svg>
                <span>Education</span>
              </h4>
              <div className="space-y-2">
                {cvData.EDUCATION.slice(0, 2).map((edu, idx) => (
                  <div key={idx} className="bg-[#E1E6E9]/30 rounded p-3 border border-[#4A5A6B]/20">
                    <p className="font-medium text-[#4A5A6B]">{edu.DEGREE}</p>
                    <p className="text-sm text-[#4A5A6B]/80">{edu.INSTITUTION}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Compact Experience */}
          {cvData.EXPERIENCE && cvData.EXPERIENCE.length > 0 && (
            <div>
              <h4 className="font-semibold text-[#4A5A6B] mb-2 flex items-center space-x-2">
                <svg className="w-4 h-4 text-[#45B39C]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6" />
                </svg>
                <span>Experience</span>
              </h4>
              <div className="space-y-2">
                {cvData.EXPERIENCE.slice(0, 2).map((exp, idx) => (
                  <div key={idx} className="bg-[#E1E6E9]/30 rounded p-3 border border-[#4A5A6B]/20">
                    <p className="font-medium text-[#4A5A6B]">{exp.TITLE}</p>
                    <p className="text-sm text-[#4A5A6B]/80">{exp.COMPANY}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Compact Skills */}
          {cvData.SKILLS && (
            <div>
              <h4 className="font-semibold text-[#4A5A6B] mb-2 flex items-center space-x-2">
                <svg className="w-4 h-4 text-[#45B39C]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <span>Key Skills</span>
              </h4>
              <div className="flex flex-wrap gap-1">
                {cvData.SKILLS.TECHNICAL && cvData.SKILLS.TECHNICAL.slice(0, 5).map((skill, idx) => (
                  <span key={idx} className="bg-[#45B39C]/10 text-[#45B39C] px-2 py-1 rounded text-xs font-medium">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center border-b border-[#4A5A6B]/20 pb-6">
          <h2 className="text-3xl font-bold text-[#4A5A6B] mb-2">{cvData.NAME || 'Unknown'}</h2>
          {cvData.LOCATION && (
            <p className="text-[#4A5A6B]/80 mb-3">{cvData.LOCATION}</p>
          )}
          {cvData.CONTACT && (
            <div className="flex flex-wrap justify-center gap-4 text-sm text-[#4A5A6B]/80">
              {cvData.CONTACT.EMAIL && (
                <span className="flex items-center space-x-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <span>{cvData.CONTACT.EMAIL}</span>
                </span>
              )}
              {cvData.CONTACT.PHONE && (
                <span className="flex items-center space-x-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                  <span>{cvData.CONTACT.PHONE}</span>
                </span>
              )}
              {cvData.CONTACT.LINKEDIN && (
                <a href={cvData.CONTACT.LINKEDIN} target="_blank" rel="noopener noreferrer" className="flex items-center space-x-1 text-blue-600 hover:text-blue-800">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                  <span>LinkedIn</span>
                </a>
              )}
              {cvData.CONTACT.GITHUB && (
                <a href={cvData.CONTACT.GITHUB} target="_blank" rel="noopener noreferrer" className="flex items-center space-x-1 text-blue-600 hover:text-blue-800">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                  <span>GitHub</span>
                </a>
              )}
            </div>
          )}
        </div>

        {/* Education */}
        {cvData.EDUCATION && cvData.EDUCATION.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-[#4A5A6B] mb-3 flex items-center space-x-2">
              <svg className="w-5 h-5 text-[#45B39C]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
              </svg>
              <span>Education</span>
            </h3>
            <div className="space-y-3">
              {cvData.EDUCATION.map((edu, index) => (
                <div key={index} className="bg-[#E1E6E9]/30 rounded-xl p-4 border border-[#4A5A6B]/20">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-semibold text-[#4A5A6B]">{edu.DEGREE}</h4>
                    {edu.PERCENTAGE && (
                      <span className="text-sm text-[#45B39C] bg-[#45B39C]/10 px-2 py-1 rounded">{edu.PERCENTAGE}</span>
                    )}
                  </div>
                  <p className="text-[#4A5A6B] font-medium">{edu.INSTITUTION}</p>
                  {edu.LOCATION && <p className="text-sm text-[#4A5A6B]/80">{edu.LOCATION}</p>}
                  {edu.DURATION && <p className="text-sm text-[#4A5A6B]/60">{edu.DURATION}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Experience */}
        {cvData.EXPERIENCE && cvData.EXPERIENCE.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-[#4A5A6B] mb-3 flex items-center space-x-2">
              <svg className="w-5 h-5 text-[#45B39C]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6" />
              </svg>
              <span>Experience</span>
            </h3>
            <div className="space-y-4">
              {cvData.EXPERIENCE.map((exp, index) => (
                <div key={index} className="bg-[#E1E6E9]/30 rounded-xl p-4 border border-[#4A5A6B]/20">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-semibold text-[#4A5A6B]">{exp.TITLE}</h4>
                    <span className="text-sm text-[#4A5A6B] bg-[#45B39C]/10 px-2 py-1 rounded">{exp.DURATION}</span>
                  </div>
                  <p className="text-[#4A5A6B] font-medium">{exp.COMPANY}</p>
                  {exp.LOCATION && <p className="text-sm text-[#4A5A6B]/80">{exp.LOCATION}</p>}
                  {exp.RESPONSIBILITIES && exp.RESPONSIBILITIES.length > 0 && (
                    <div className="mt-3">
                      <p className="text-sm font-medium text-[#4A5A6B] mb-1">Key Responsibilities:</p>
                      <ul className="list-disc list-inside text-sm text-[#4A5A6B]/80 space-y-1">
                        {exp.RESPONSIBILITIES.map((resp, idx) => (
                          <li key={idx}>{resp}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Skills */}
        {cvData.SKILLS && (
          <div>
            <h3 className="text-lg font-semibold text-[#4A5A6B] mb-3 flex items-center space-x-2">
              <svg className="w-5 h-5 text-[#45B39C]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <span>Skills</span>
            </h3>
            <div className="space-y-4">
              {cvData.SKILLS.TECHNICAL && cvData.SKILLS.TECHNICAL.length > 0 && (
                <div>
                  <h4 className="font-medium text-[#4A5A6B] mb-2">Technical Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {cvData.SKILLS.TECHNICAL.map((skill, index) => (
                      <span key={index} className="bg-[#45B39C]/10 text-[#45B39C] px-3 py-1 rounded-full text-sm font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {cvData.SKILLS.LANGUAGES && cvData.SKILLS.LANGUAGES.length > 0 && (
                <div>
                  <h4 className="font-medium text-[#4A5A6B] mb-2">Programming Languages</h4>
                  <div className="flex flex-wrap gap-2">
                    {cvData.SKILLS.LANGUAGES.map((skill, index) => (
                      <span key={index} className="bg-[#FCD462]/20 text-[#D4A81E] px-3 py-1 rounded-full text-sm font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {cvData.SKILLS.TOOLS && cvData.SKILLS.TOOLS.length > 0 && (
                <div>
                  <h4 className="font-medium text-[#4A5A6B] mb-2">Tools & Technologies</h4>
                  <div className="flex flex-wrap gap-2">
                    {cvData.SKILLS.TOOLS.map((skill, index) => (
                      <span key={index} className="bg-[#64798A]/10 text-[#64798A] px-3 py-1 rounded-full text-sm font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {cvData.SKILLS.SOFT_SKILLS && cvData.SKILLS.SOFT_SKILLS.length > 0 && (
                <div>
                  <h4 className="font-medium text-[#4A5A6B] mb-2">Soft Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {cvData.SKILLS.SOFT_SKILLS.map((skill, index) => (
                      <span key={index} className="bg-[#4A5A6B]/10 text-[#4A5A6B] px-3 py-1 rounded-full text-sm font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Certifications */}
        {cvData.CERTIFICATIONS && cvData.CERTIFICATIONS.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-[#4A5A6B] mb-3 flex items-center space-x-2">
              <svg className="w-5 h-5 text-[#FCD462]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
              <span>Certifications</span>
            </h3>
            <div className="space-y-2">
              {cvData.CERTIFICATIONS.map((cert, index) => (
                <div key={index} className="bg-[#E1E6E9]/30 rounded-xl p-3 border border-[#4A5A6B]/20">
                  <p className="text-[#4A5A6B]">{cert}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Projects */}
        {cvData.PROJECTS && cvData.PROJECTS.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-[#4A5A6B] mb-3 flex items-center space-x-2">
              <svg className="w-5 h-5 text-[#45B39C]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <span>Projects</span>
            </h3>
            <div className="space-y-2">
              {cvData.PROJECTS.map((project, index) => (
                <div key={index} className="bg-[#E1E6E9]/30 rounded-xl p-3 border border-[#4A5A6B]/20">
                  <p className="text-[#4A5A6B]">{project}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Miscellaneous */}
        {cvData.MISCELLANEOUS && (
          <div>
            <h3 className="text-lg font-semibold text-[#4A5A6B] mb-3 flex items-center space-x-2">
              <svg className="w-5 h-5 text-[#45B39C]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Additional Information</span>
            </h3>
            <div className="bg-[#E1E6E9]/30 rounded-xl p-4 border border-[#4A5A6B]/20">
              <p className="text-[#4A5A6B]">{cvData.MISCELLANEOUS}</p>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Function to handle candidate selection for comparison
  const handleCandidateSelect = (index) => {
    setSelectedCandidates(prev => {
      if (prev.includes(index)) {
        return prev.filter(i => i !== index);
      } else {
        return [...prev, index].slice(0, 3); // Limit to 3 candidates for comparison
      }
    });
  };

  // Determine response type and render accordingly
  const renderResponse = () => {
    // Check if we have structured data
    if (structured_data && structured_data.length > 0) {
      if (structured_data.length === 1) {
        return renderStructuredCV(structured_data[0]);
      } else {
        return (
          <div className="space-y-6">
            {/* Multiple Candidates Header */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                Multiple Candidates Found
              </h3>
              <p className="text-blue-700 mb-4">
                Found {structured_data.length} unique candidates matching your query.
              </p>
              
              {/* View Mode Toggle */}
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    viewMode === 'list' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-white text-blue-600 border border-blue-200 hover:bg-blue-50'
                  }`}
                >
                  List View
                </button>
                <button
                  onClick={() => setViewMode('compare')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    viewMode === 'compare' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-white text-blue-600 border border-blue-200 hover:bg-blue-50'
                  }`}
                >
                  Compare View
                </button>
              </div>
            </div>
            
            {/* Comparison View */}
            {viewMode === 'compare' && selectedCandidates.length > 0 && (
              <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Comparing {selectedCandidates.length} Candidates
                  </h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
                  {selectedCandidates.map((index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      {renderStructuredCV(structured_data[index], index, true)}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Candidate List */}
            <div className="space-y-4">
              {structured_data.map((cvData, index) => (
                <div key={index} className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
                  <div className="bg-gradient-to-r from-indigo-50 to-purple-50 px-6 py-4 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xl font-bold text-gray-900 flex items-center space-x-2">
                        <span className="bg-indigo-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
                          {index + 1}
                        </span>
                        <span>{cvData.NAME || 'Unknown'}</span>
                      </h3>
                      
                      {/* Selection Checkbox for Comparison */}
                      {viewMode === 'compare' && (
                        <label className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selectedCandidates.includes(index)}
                            onChange={() => handleCandidateSelect(index)}
                            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                          />
                          <span className="text-sm text-gray-600">Compare</span>
                        </label>
                      )}
                    </div>
                  </div>
                  <div className="p-6">
                    {renderStructuredCV(cvData, index, viewMode === 'compare')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      }
    }
    
    // Fallback to raw answer if no structured data
    return (
      <div className="prose prose-gray max-w-none">
        <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{answer}</p>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Answer Card */}
      <div className="bg-white rounded-2xl shadow-xl border border-gray-200/50 overflow-hidden">
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 px-6 py-4 border-b border-gray-200/50">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Search Results</span>
          </h3>
        </div>
        <div className="p-6">
          {renderResponse()}
        </div>
      </div>

      {/* Raw Sources Toggle */}
      {sources && sources.length > 0 && (
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200/50 overflow-hidden">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200/50">
            <button
              onClick={() => setExpandedSources(!expandedSources)}
              className="flex items-center justify-between w-full text-left"
            >
              <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <span>Raw Source Data ({sources.length})</span>
              </h3>
              <svg 
                className={`w-5 h-5 text-blue-600 transition-transform ${expandedSources ? 'rotate-180' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
          
          {expandedSources && (
            <div className="p-6">
              <div className="space-y-4">
                {sources.map((source, index) => (
                  <div key={index} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-blue-600">{index + 1}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <pre className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap font-sans">
                          {source}
                        </pre>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AnswerCard;
