const API_BASE_URL = 'http://localhost:8000';

export const cvApi = {
  async askQuestion(question) {
    try {
      const response = await fetch(`${API_BASE_URL}/ask/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Return the data with structured_data field
      return {
        answer: data.answer || '',
        sources: data.sources || [],
        structured_data: data.structured_data || [],
        error: data.error || null
      };
    } catch (error) {
      console.error('Error asking question:', error);
      throw error;
    }
  },

  async uploadCV(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/upload/`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error uploading CV:', error);
      throw error;
    }
  }
}; 