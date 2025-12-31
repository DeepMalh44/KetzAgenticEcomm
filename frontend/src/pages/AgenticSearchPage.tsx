import { useState, useEffect, useCallback, useRef } from 'react'
import ProductGrid from '../components/ProductGrid'
import CrossSellPanel from '../components/CrossSellPanel'
import ImageSearch from '../components/ImageSearch'
import VoiceAssistant from '../components/VoiceAssistant'
import ChatPanel from '../components/ChatPanel'
import { useAppStore } from '../store/appStore'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

interface AgenticSearchPageProps {
  realtimeSession: ReturnType<typeof import('../hooks/useRealtimeSession').useRealtimeSession>
  showImageSearch: boolean
  setShowImageSearch: (show: boolean) => void
}

export default function AgenticSearchPage({ realtimeSession, showImageSearch, setShowImageSearch }: AgenticSearchPageProps) {
  const { 
    products, 
    isLoading, 
    searchQuery, 
    setSearchQuery, 
    setProducts, 
    setLoading,
    isVoiceSearchResult,
    setSearchMode,
  } = useAppStore()

  // Set search mode to agentic when this page loads
  useEffect(() => {
    setSearchMode('agentic')
  }, [setSearchMode])

  // State for LLM response and activity
  const [llmResponse, setLlmResponse] = useState<string | null>(null)
  const [showActivity, setShowActivity] = useState(false)
  const [activity, setActivity] = useState<any>(null)

  // Track if initial load has happened
  const initialLoadDone = useRef(false)

  // Fetch products using Agentic Retrieval
  const fetchProducts = useCallback(async (query?: string) => {
    setLoading(true)
    setLlmResponse(null)
    setActivity(null)
    
    try {
      if (query) {
        // Use agentic retrieval for search queries
        const response = await fetch(`${BACKEND_URL}/api/v1/agentic/search`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: query,
            top: 20,
            include_activity: showActivity
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          setProducts(data.products || [])
          
          // Capture LLM response if available
          if (data.llm_response) {
            setLlmResponse(data.llm_response)
          }
          
          // Capture activity/query plan if available
          if (data.activity) {
            setActivity(data.activity)
          }
        } else {
          console.error('Agentic search failed:', response.status)
          // Fallback to regular search
          const fallbackResponse = await fetch(`${BACKEND_URL}/api/v1/products/search?query=${encodeURIComponent(query)}&limit=20`)
          if (fallbackResponse.ok) {
            const data = await fallbackResponse.json()
            setProducts(data.products || [])
          }
        }
      } else {
        // No query - get all products using regular endpoint
        const url = `${BACKEND_URL}/api/v1/products/?limit=20`
        const response = await fetch(url)
        if (response.ok) {
          const data = await response.json()
          setProducts(data.products || [])
        }
      }
    } catch (error) {
      console.error('Failed to fetch products:', error)
    } finally {
      setLoading(false)
    }
  }, [setProducts, setLoading, showActivity])

  // Load initial products (only once on mount)
  useEffect(() => {
    if (!initialLoadDone.current) {
      initialLoadDone.current = true
      fetchProducts()
    }
  }, [])

  // Search with debounce (only for typed search, not voice)
  useEffect(() => {
    if (isVoiceSearchResult) {
      return
    }
    
    if (!initialLoadDone.current) {
      return
    }
    
    const timer = setTimeout(() => {
      if (searchQuery.trim()) {
        fetchProducts(searchQuery)
      } else {
        fetchProducts()
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [searchQuery, isVoiceSearchResult])

  return (
    <>
      {/* Main Content */}
      <div className="flex h-[calc(100vh-64px)]">
        {/* Left Panel - Products */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            {/* Page Title - indicates Agentic Retrieval */}
            <div className="mb-4 flex items-center gap-2 flex-wrap">
              <span className="px-3 py-1 text-xs font-semibold bg-purple-100 text-purple-700 rounded-full">
                Agentic Retrieval (Preview)
              </span>
              <span className="text-sm text-slate-500">
                Powered by Azure AI Search Knowledge Base with LLM-assisted query planning
              </span>
              <label className="ml-auto flex items-center gap-2 text-sm text-slate-600">
                <input
                  type="checkbox"
                  checked={showActivity}
                  onChange={(e) => setShowActivity(e.target.checked)}
                  className="rounded border-slate-300 text-purple-600 focus:ring-purple-500"
                />
                Show Query Plan
              </label>
            </div>

            {/* LLM Response Card */}
            {llmResponse && (
              <div className="mb-4 p-4 bg-purple-50 border border-purple-200 rounded-xl">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-purple-800 mb-1">AI Assistant Response</h4>
                    <p className="text-sm text-purple-700">{llmResponse}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Activity/Query Plan Card */}
            {showActivity && activity && (
              <div className="mb-4 p-4 bg-slate-50 border border-slate-200 rounded-xl">
                <h4 className="text-sm font-semibold text-slate-800 mb-2">Query Plan</h4>
                <pre className="text-xs text-slate-600 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(activity, null, 2)}
                </pre>
              </div>
            )}

            {/* Search Bar */}
            <div className="mb-6">
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Try conversational queries like 'I need to fix a leaky faucet' or 'What tools do I need for deck building?'"
                  className="w-full px-4 py-3 pl-12 text-lg border border-purple-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white shadow-sm"
                />
                <svg
                  className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              </div>
            </div>

            {/* Category Pills */}
            <div className="flex flex-wrap gap-2 mb-6">
              {['All', 'Power Tools', 'Hand Tools', 'Paint', 'Flooring', 'Plumbing', 'Electrical', 'Outdoor'].map((cat) => (
                <button
                  key={cat}
                  className="px-4 py-2 rounded-full text-sm font-medium bg-white border border-slate-200 hover:bg-purple-50 hover:border-purple-300 hover:text-purple-700 transition-colors"
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Products Grid */}
            <ProductGrid products={products} isLoading={isLoading} />

            {/* Cross-Sell Recommendations */}
            <CrossSellPanel />
          </div>
        </main>

        {/* Right Panel - Voice Assistant & Chat */}
        <aside className="w-96 border-l border-slate-200 bg-white flex flex-col">
          <VoiceAssistant realtimeSession={realtimeSession} />
          <ChatPanel realtimeSession={realtimeSession} />
        </aside>
      </div>

      {/* Image Search Modal */}
      {showImageSearch && (
        <ImageSearch onClose={() => setShowImageSearch(false)} />
      )}
    </>
  )
}
