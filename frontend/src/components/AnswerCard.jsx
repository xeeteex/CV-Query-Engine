import React, { useState } from 'react';

// Format source data with syntax highlighting and better formatting
const formatSourceData = (source) => {
  try {
    // Try to parse as JSON for pretty printing
    const parsed = JSON.parse(source);
    return JSON.stringify(parsed, null, 2);
  } catch (e) {
    // If not JSON, try to format as key-value pairs
    if (typeof source === 'string' && source.includes(':')) {
      return source
        .split('\n')
        .map(line => {
          // Add indentation for nested objects/arrays
          const indent = (line.match(/^\s*/) || [''])[0].length / 2;
          const trimmed = line.trim();
          
          // Add syntax highlighting for keys and values
          if (trimmed.endsWith('{') || trimmed.endsWith('[') || trimmed.endsWith('}') || trimmed.endsWith(']')) {
            return '  '.repeat(indent) + `<span class="text-purple-600">${trimmed}</span>`;
          }
          
          const [key, ...valueParts] = trimmed.split(':');
          const value = valueParts.join(':');
          
          if (!key || !value) return '  '.repeat(indent) + trimmed;
          
          return `  ${'  '.repeat(indent)}<span class="text-blue-600">${key.trim()}</span>: <span class="text-gray-800">${value.trim()}</span>`;
        })
        .join('\n');
    }
    
    // Return as is if no special formatting applies
    return source;
  }
};

const AnswerCard = ({ answer, sources, structured_data }) => {
  const [expandedSources, setExpandedSources] = useState(false);
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'compare'
  
  if (!answer) return null;

  // Function to render structured CV data
  const renderStructuredCV = (cvData, index = null, isCompact = false) => {
    if (isCompact) {
      // Calculate total years of experience if available
      const totalExperience = cvData.EXPERIENCE?.reduce((total, exp) => {
        if (exp.DURATION) {
          // Simple extraction of years from duration string (e.g., "2 years" -> 2)
          const yearsMatch = exp.DURATION.match(/(\d+)\s*(?:year|yr|y)/i);
          if (yearsMatch) return total + parseInt(yearsMatch[1], 10);
        }
        return total;
      }, 0);

      return (
        <div className="space-y-6">
          {/* Compact Header */}
          <div className="text-center">
            <div className="w-20 h-20 mx-auto mb-3 rounded-full bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center text-2xl font-bold text-indigo-600 border-2 border-white shadow-sm">
              {cvData.NAME ? cvData.NAME.charAt(0).toUpperCase() : '?'}
            </div>
            <h3 className="text-xl font-bold text-gray-900">{cvData.NAME || 'Unknown Candidate'}</h3>
            
            <div className="flex flex-wrap items-center justify-center gap-2 mt-2">
              {totalExperience > 0 && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {totalExperience}+ years experience
                </span>
              )}
              {cvData.LOCATION && (
                <span className="inline-flex items-center text-sm text-gray-600">
                  <svg className="w-3.5 h-3.5 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {cvData.LOCATION}
                </span>
              )}
            </div>
            
            {cvData.EMAIL && (
              <a 
                href={`mailto:${cvData.EMAIL}`}
                className="inline-block mt-2 text-sm text-blue-600 hover:text-blue-800 hover:underline"
                title="Email candidate"
              >
                {cvData.EMAIL}
              </a>
            )}
          </div>

          {/* Compact Education */}
          {cvData.EDUCATION && cvData.EDUCATION.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-semibold text-[#4A5A6B] flex items-center space-x-2 text-sm uppercase tracking-wider text-gray-500">
                <svg className="w-4 h-4 text-[#45B39C]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                </svg>
                <span>Education</span>
              </h4>
              <div className="space-y-3">
                {cvData.EDUCATION.slice(0, 2).map((edu, idx) => (
                  <div key={idx} className="bg-white rounded-lg shadow-sm border border-gray-100 p-4 hover:shadow-md transition-shadow duration-200">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-semibold text-gray-800">{edu.DEGREE || 'Degree not specified'}</p>
                        <p className="text-sm text-gray-600 mt-1">{edu.INSTITUTION || 'Institution not specified'}</p>
                      </div>
                      {edu.DURATION && (
                        <span className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded-full">
                          {edu.DURATION}
                        </span>
                      )}
                    </div>
                    {edu.FIELD_OF_STUDY && (
                      <p className="text-xs text-gray-500 mt-2">
                        <span className="font-medium">Field:</span> {edu.FIELD_OF_STUDY}
                      </p>
                    )}
                  </div>
                ))}
                {cvData.EDUCATION.length > 2 && (
                  <p className="text-xs text-gray-500 text-center">+{cvData.EDUCATION.length - 2} more education entries</p>
                )}
              </div>
            </div>
          )}

          {/* Compact Experience */}
          {cvData.EXPERIENCE && cvData.EXPERIENCE.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-semibold text-[#4A5A6B] flex items-center space-x-2 text-sm uppercase tracking-wider text-gray-500">
                <svg className="w-4 h-4 text-[#45B39C]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6" />
                </svg>
                <span>Experience</span>
              </h4>
              <div className="space-y-3">
                {cvData.EXPERIENCE.slice(0, 2).map((exp, idx) => (
                  <div key={idx} className="bg-white rounded-lg shadow-sm border border-gray-100 p-4 hover:shadow-md transition-shadow duration-200">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-semibold text-gray-800">{exp.TITLE || 'Position not specified'}</p>
                        <p className="text-sm text-gray-600 mt-1">{exp.COMPANY || 'Company not specified'}</p>
                      </div>
                      {exp.DURATION && (
                        <span className="text-xs bg-green-50 text-green-600 px-2 py-1 rounded-full whitespace-nowrap">
                          {exp.DURATION}
                        </span>
                      )}
                    </div>
                    {exp.LOCATION && (
                      <p className="text-xs text-gray-500 mt-1 flex items-center">
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        {exp.LOCATION}
                      </p>
                    )}
                    {exp.RESPONSIBILITIES && exp.RESPONSIBILITIES.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs text-gray-500 font-medium mb-1">Key Responsibilities:</p>
                        <ul className="text-xs text-gray-600 space-y-1">
                          {exp.RESPONSIBILITIES.slice(0, 2).map((resp, idx) => (
                            <li key={idx} className="flex items-start">
                              <span className="text-[#45B39C] mr-2">•</span>
                              <span className="flex-1">{resp}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
                {cvData.EXPERIENCE.length > 2 && (
                  <p className="text-xs text-gray-500 text-center">+{cvData.EXPERIENCE.length - 2} more positions</p>
                )}
              </div>
            </div>
          )}

          {/* Compact Skills */}
          {cvData.SKILLS && (
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-500 flex items-center space-x-2 text-sm uppercase tracking-wider">
                <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0114 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <span>Key Skills</span>
              </h4>
              
              {/* Technical Skills */}
              {cvData.SKILLS.TECHNICAL && cvData.SKILLS.TECHNICAL.length > 0 && (
                <div className="mb-3">
                  <h5 className="text-xs font-medium text-gray-500 mb-2">TECHNICAL</h5>
                  <div className="flex flex-wrap gap-2">
                    {cvData.SKILLS.TECHNICAL.slice(0, 8).map((skill, idx) => (
                      <span 
                        key={`tech-${idx}`} 
                        className="bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full text-xs font-medium hover:bg-indigo-100 transition-colors"
                        title={skill}
                      >
                        {skill.length > 15 ? `${skill.substring(0, 15)}...` : skill}
                      </span>
                    ))}
                    {cvData.SKILLS.TECHNICAL.length > 8 && (
                      <span className="text-xs text-gray-500 self-center">
                        +{cvData.SKILLS.TECHNICAL.length - 8} more
                      </span>
                    )}
                  </div>
                </div>
              )}
              
              {/* Soft Skills */}
              {cvData.SKILLS.SOFT && cvData.SKILLS.SOFT.length > 0 && (
                <div className="mb-3">
                  <h5 className="text-xs font-medium text-gray-500 mb-2">SOFT SKILLS</h5>
                  <div className="flex flex-wrap gap-2">
                    {cvData.SKILLS.SOFT.slice(0, 5).map((skill, idx) => (
                      <span 
                        key={`soft-${idx}`} 
                        className="bg-green-50 text-green-700 px-3 py-1 rounded-full text-xs font-medium hover:bg-green-100 transition-colors"
                        title={skill}
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Tools & Technologies */}
              {cvData.SKILLS.TOOLS && cvData.SKILLS.TOOLS.length > 0 && (
                <div>
                  <h5 className="text-xs font-medium text-gray-500 mb-2">TOOLS & TECHNOLOGIES</h5>
                  <div className="flex flex-wrap gap-2">
                    {cvData.SKILLS.TOOLS.slice(0, 6).map((tool, idx) => (
                      <span 
                        key={`tool-${idx}`} 
                        className="bg-amber-50 text-amber-700 px-3 py-1 rounded-full text-xs font-medium hover:bg-amber-100 transition-colors"
                        title={tool}
                      >
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )}
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
                  <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                            <span className="text-xs font-medium text-blue-600">{index + 1}</span>
                          </div>
                          <span className="text-xs font-medium text-gray-500">Source {index + 1}</span>
                        </div>
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            navigator.clipboard.writeText(source);
                          }}
                          className="text-xs text-blue-600 hover:text-blue-800 flex items-center space-x-1"
                          title="Copy to clipboard"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                          </svg>
                          <span>Copy</span>
                        </button>
                      </div>
                    </div>
                    <div className="p-4">
                      <div className="bg-gray-50 p-3 rounded-lg overflow-auto max-h-60">
                        <pre 
                          className="text-xs text-gray-700 leading-relaxed whitespace-pre-wrap font-mono"
                          dangerouslySetInnerHTML={{ __html: formatSourceData(source) }}
                        />
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
