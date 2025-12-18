import { useState, useEffect, useCallback, useRef } from 'react'
import ProductGrid from '../components/ProductGrid'
import ImageSearch from '../components/ImageSearch'
import VoiceAssistant from '../components/VoiceAssistant'
import ChatPanel from '../components/ChatPanel'
import { useAppStore } from '../store/appStore'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

interface HomePageProps {
  realtimeSession: ReturnType<typeof import('../hooks/useRealtimeSession').useRealtimeSession>
  showImageSearch: boolean
  setShowImageSearch: (show: boolean) => void
}

export default function HomePage({ realtimeSession, showImageSearch, setShowImageSearch }: HomePageProps) {
  const { 
    products, 
    isLoading, 
    searchQuery, 
    setSearchQuery, 
    setProducts, 
    setLoading,
    isVoiceSearchResult,
  } = useAppStore()

  // Track if initial load has happened
  const initialLoadDone = useRef(false)

  // Fetch products - either search or get all (using semantic search)
  const fetchProducts = useCallback(async (query?: string) => {
    setLoading(true)
    try {
      const url = query 
        ? `${BACKEND_URL}/api/v1/products/search?query=${encodeURIComponent(query)}&limit=20`
        : `${BACKEND_URL}/api/v1/products/?limit=20`
      
      const response = await fetch(url)
      if (response.ok) {
        const data = await response.json()
        setProducts(data.products || [])
      }
    } catch (error) {
      console.error('Failed to fetch products:', error)
    } finally {
      setLoading(false)
    }
  }, [setProducts, setLoading])

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
            {/* Page Title - indicates Semantic Search */}
            <div className="mb-4 flex items-center gap-2">
              <span className="px-3 py-1 text-xs font-semibold bg-blue-100 text-blue-700 rounded-full">
                Semantic Search
              </span>
              <span className="text-sm text-slate-500">
                Powered by Azure AI Search with vector embeddings
              </span>
            </div>

            {/* Search Bar */}
            <div className="mb-6">
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search for tools, materials, paint, and more..."
                  className="w-full px-4 py-3 pl-12 text-lg border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white shadow-sm"
                />
                <svg
                  className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
            </div>

            {/* Category Pills */}
            <div className="flex flex-wrap gap-2 mb-6">
              {['All', 'Power Tools', 'Hand Tools', 'Paint', 'Flooring', 'Plumbing', 'Electrical', 'Outdoor'].map((cat) => (
                <button
                  key={cat}
                  className="px-4 py-2 rounded-full text-sm font-medium bg-white border border-slate-200 hover:bg-primary-50 hover:border-primary-300 hover:text-primary-700 transition-colors"
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Products Grid */}
            <ProductGrid products={products} isLoading={isLoading} />
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
