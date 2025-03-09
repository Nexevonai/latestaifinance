'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Source {
  title?: string;
  url?: string;
}

interface SearchResult {
  answer: string;
  sources?: Source[];
  data?: any;
  session_id?: string;
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('sonar'); // 'sonar' or 'deep_research'
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [error, setError] = useState('');
  const [statusMessages, setStatusMessages] = useState<string[]>([]);
  const [useStreaming, setUseStreaming] = useState(true);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [conversationHistory, setConversationHistory] = useState<{query: string, answer: string}[]>([]);
  const [showDeepResearchConfirm, setShowDeepResearchConfirm] = useState(false);
  
  const router = useRouter();
  const abortControllerRef = useRef<AbortController | null>(null);
  const resultContainerRef = useRef<HTMLDivElement>(null);
  
  // Clean up any ongoing fetch when component unmounts
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Scroll to result when it's available
  useEffect(() => {
    if (result && resultContainerRef.current) {
      resultContainerRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [result]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    // Check if deep research mode is requested and needs confirmation
    if (mode === 'deep_research' && !showDeepResearchConfirm) {
      setShowDeepResearchConfirm(true);
      return;
    }

    // Reset confirmation state if proceeding
    if (showDeepResearchConfirm) {
      setShowDeepResearchConfirm(false);
    }
    
    setLoading(true);
    setError('');
    setResult(null);
    setStatusMessages([]);
    
    // Abort any ongoing fetch
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create a new AbortController
    abortControllerRef.current = new AbortController();
    
    try {
      if (useStreaming) {
        // Streaming approach
        const response = await fetch('http://localhost:8000/api/search/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query,
            mode,
            session_id: sessionId
          }),
          signal: abortControllerRef.current.signal,
        });
        
        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('Failed to get response reader');
        }
        
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          
          // Process complete lines
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep the last incomplete line in the buffer
          
          for (const line of lines) {
            if (!line.trim()) continue;
            
            try {
              const data = JSON.parse(line);
              
              if (data.type === 'status') {
                setStatusMessages(prev => [...prev, data.content]);
                // Store session ID if provided
                if (data.session_id && !sessionId) {
                  setSessionId(data.session_id);
                }
              } else if (data.type === 'result') {
                setResult({
                  answer: data.content,
                  sources: data.sources || [],
                  session_id: data.session_id
                });
                // Store session ID if provided
                if (data.session_id && !sessionId) {
                  setSessionId(data.session_id);
                }
                // Add to conversation history
                setConversationHistory(prev => [...prev, {
                  query: query,
                  answer: data.content
                }]);
                setLoading(false);
              } else if (data.type === 'error') {
                setError(data.content);
                // Store session ID if provided
                if (data.session_id && !sessionId) {
                  setSessionId(data.session_id);
                }
                setLoading(false);
              }
            } catch (e) {
              console.error('Error parsing JSON:', e, line);
            }
          }
        }
      } else {
        // Non-streaming approach
        const response = await fetch('http://localhost:8000/api/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query,
            mode,
            session_id: sessionId
          }),
          signal: abortControllerRef.current.signal,
        });
        
        const data = await response.json();
        setResult(data);
        
        // Store session ID if provided
        if (data.session_id && !sessionId) {
          setSessionId(data.session_id);
        }
        
        // Add to conversation history
        setConversationHistory(prev => [...prev, {
          query: query,
          answer: data.answer
        }]);
        
        setLoading(false);
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Error:', error);
        setError('An error occurred while searching. Please try again.');
      }
      setLoading(false);
    }
  };

  const handleCancelDeepResearch = () => {
    setShowDeepResearchConfirm(false);
    setMode('sonar');
  };

  const handleNewSearch = () => {
    setQuery('');
    setResult(null);
    setError('');
    setStatusMessages([]);
    setShowDeepResearchConfirm(false);
  };
  
  return (
    <main className="min-h-screen p-6 md:p-24 bg-gray-50">
      <div className="max-w-5xl mx-auto">
        <div className="mb-12 text-center">
          <h1 className="text-3xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-teal-600 text-transparent bg-clip-text flex items-center justify-center">
            <svg className="w-8 h-8 mr-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-600"/>
            </svg>
            AI Financial Search
          </h1>
          
          <p className="text-gray-600 mb-8">
            Ask anything about stocks, markets, and investment decisions
          </p>
          
          {sessionId && (
            <div className="text-sm text-gray-500 mb-4">
              Session ID: {sessionId}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter your financial question..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-2 bg-blue-600 text-white font-medium rounded-full hover:bg-blue-700 transition-colors disabled:bg-blue-400"
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
              </div>
            </div>
            
            <div className="flex items-center justify-center gap-6">
              <div className="flex items-center">
                <input
                  type="radio"
                  id="sonar"
                  name="mode"
                  value="sonar"
                  checked={mode === 'sonar'}
                  onChange={() => setMode('sonar')}
                  className="mr-2"
                />
                <label htmlFor="sonar">Perplexity Sonar</label>
              </div>
              
              <div className="flex items-center">
                <input
                  type="radio"
                  id="deep_research"
                  name="mode"
                  value="deep_research"
                  checked={mode === 'deep_research'}
                  onChange={() => setMode('deep_research')}
                  className="mr-2"
                />
                <label htmlFor="deep_research">Deep Research</label>
              </div>
              
              <div className="flex items-center ml-4">
                <input
                  type="checkbox"
                  id="streaming"
                  checked={useStreaming}
                  onChange={(e) => setUseStreaming(e.target.checked)}
                  className="mr-2"
                />
                <label htmlFor="streaming">Enable Streaming</label>
              </div>
            </div>
          </form>
          
          {error && <div className="mt-4 text-red-500">{error}</div>}
          
          {showDeepResearchConfirm && (
            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h3 className="text-lg font-medium mb-2">Deep Research Mode</h3>
              <p className="mb-4">Deep Research mode will take longer but provide a more comprehensive analysis with detailed comparisons and sources.</p>
              <div className="flex justify-center gap-4">
                <button 
                  onClick={handleSubmit}
                  className="px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
                >
                  Proceed with Deep Research
                </button>
                <button 
                  onClick={handleCancelDeepResearch}
                  className="px-4 py-2 bg-gray-200 text-gray-800 font-medium rounded-md hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
          
          {!result && !loading && statusMessages.length === 0 && !showDeepResearchConfirm && (
            <div className="mt-8 text-gray-500 text-sm">
              <p>Examples:</p>
              <div className="flex flex-wrap justify-center gap-2 mt-2">
                <button 
                  onClick={() => setQuery("What's the sentiment around NVDA?")}
                  className="text-blue-500 hover:underline"
                >
                  What's the sentiment around NVDA?
                </button>
                <span>|</span>
                <button 
                  onClick={() => setQuery("Compare AAPL and MSFT fundamentals")}
                  className="text-blue-500 hover:underline"
                >
                  Compare AAPL and MSFT fundamentals
                </button>
                <span>|</span>
                <button 
                  onClick={() => setQuery("Should I buy Tesla stock?")}
                  className="text-blue-500 hover:underline"
                >
                  Should I buy Tesla stock?
                </button>
              </div>
            </div>
          )}
        </div>
        
        {loading && (
          <div className="bg-white rounded-xl shadow-md p-6 mb-8">
            <div className="flex justify-center items-center mb-6">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="ml-4 text-lg">The AI analysts are researching your question...</p>
            </div>
            
            {statusMessages.length > 0 && (
              <div className="mt-4 border-t pt-4">
                <h3 className="text-lg font-medium mb-2">Progress Updates:</h3>
                <ul className="space-y-2">
                  {statusMessages.map((message, index) => (
                    <li key={index} className="flex items-center">
                      <span className="mr-2 text-blue-500">•</span>
                      {message}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        
        {result && !loading && (
          <div ref={resultContainerRef} className="bg-white rounded-xl shadow-md p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">Search Results</h2>
            <div className="prose prose-blue max-w-none">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({node, ...props}) => <h1 className="text-2xl font-bold mt-6 mb-4 text-gray-800" {...props} />,
                  h2: ({node, ...props}) => <h2 className="text-xl font-bold mt-5 mb-3 text-gray-800" {...props} />,
                  h3: ({node, ...props}) => <h3 className="text-lg font-bold mt-4 mb-2 text-gray-800" {...props} />,
                  h4: ({node, ...props}) => <h4 className="text-base font-bold mt-3 mb-2 text-gray-800" {...props} />,
                  p: ({node, ...props}) => <p className="my-3 text-gray-700" {...props} />,
                  ul: ({node, ...props}) => <ul className="list-disc pl-6 my-3" {...props} />,
                  ol: ({node, ...props}) => <ol className="list-decimal pl-6 my-3" {...props} />,
                  li: ({node, ...props}) => <li className="mb-1" {...props} />,
                  a: ({node, ...props}) => <a className="text-blue-600 hover:underline" {...props} />,
                  blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-gray-200 pl-4 italic my-4" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-bold text-gray-900" {...props} />,
                  code: ({node, ...props}) => <code className="bg-gray-100 rounded px-1 py-0.5 text-sm" {...props} />,
                }}
              >
                {result.answer}
              </ReactMarkdown>
            </div>
            
            {result.sources && result.sources.length > 0 && (
              <div className="mt-8 border-t pt-4">
                <h3 className="text-lg font-medium mb-2">Sources</h3>
                <ul className="space-y-2 pl-4">
                  {result.sources.map((source: Source, index: number) => (
                    <li key={index} className="flex items-start">
                      <span className="mr-2 text-blue-500 mt-1">•</span>
                      <a
                        href={source.url}
          target="_blank"
          rel="noopener noreferrer"
                        className="text-blue-600 hover:underline break-words"
                      >
                        {source.title || source.url || "Source"}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            <div className="mt-8 border-t pt-4">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="flex flex-col md:flex-row gap-4">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="Ask a follow-up question..."
                      className="w-full px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
                    />
                    <button
                      type="submit"
                      disabled={loading}
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-2 bg-blue-600 text-white font-medium rounded-full hover:bg-blue-700 transition-colors disabled:bg-blue-400"
                    >
                      Search
                    </button>
                  </div>
                </div>
              </form>
              
              <div className="mt-4 flex justify-center">
                <button
                  onClick={handleNewSearch}
                  className="px-4 py-2 bg-gray-200 text-gray-800 font-medium rounded-md hover:bg-gray-300 transition-colors"
                >
                  Start New Search
                </button>
              </div>
            </div>
          </div>
        )}
        
        {conversationHistory.length > 0 && (
          <div className="mt-8 bg-white rounded-xl shadow-md p-6">
            <h3 className="text-lg font-medium mb-4">Conversation History</h3>
            <div className="space-y-4">
              {conversationHistory.map((item, index) => (
                <div key={index} className="border-b pb-4">
                  <p className="font-medium text-blue-600">You: {item.query}</p>
                  <div className="mt-2 text-gray-700">
                    <p>AI: {item.answer.length > 150 ? `${item.answer.substring(0, 150)}...` : item.answer}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="text-center text-sm text-gray-500 mt-12">
          <p>Powered by AI Hedge Fund | For educational purposes only | Not financial advice</p>
          <p className="mt-1">This tool is for research and learning only. Always consult with a financial advisor before making investment decisions.</p>
        </div>
    </div>
    </main>
  );
}
