import { useState, useEffect, useCallback, useRef } from 'react'
import { BrowserRouter as Router } from 'react-router-dom'
import Header from './components/Header'
import VoiceAssistant from './components/VoiceAssistant'
import ProductGrid from './components/ProductGrid'
import ImageSearch from './components/ImageSearch'
import ChatPanel from './components/ChatPanel'
import CartPanel from './components/CartPanel'
import OrdersPanel from './components/OrdersPanel'
import { useAppStore } from './store/appStore'
import { useRealtimeSession } from './hooks/useRealtimeSession'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

function App() {
  const [showImageSearch, setShowImageSearch] = useState(false)
  const { 
    products, 
    isLoading, 
    searchQuery, 
    setSearchQuery, 
    setProducts, 
    setLoading,
    isCartOpen,
    setCartOpen,
    isOrdersOpen,
    setOrdersOpen,
    isVoiceSearchResult,
  } = useAppStore()

  // Shared realtime session for voice and chat
  const realtimeSession = useRealtimeSession()

  // Track if initial load has happened
  const initialLoadDone = useRef(false)

  // Fetch products - either search or get all
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
  }, []) // Empty deps - only run once on mount

  // Search with debounce (only for typed search, not voice)
  useEffect(() => {
    // Don't auto-fetch if we have voice/image search results
    if (isVoiceSearchResult) {
      return
    }
    
    // Skip if this is the initial mount (handled above)
    if (!initialLoadDone.current) {
      return
    }
    
    const timer = setTimeout(() => {
      if (searchQuery.trim()) {
        fetchProducts(searchQuery)
      } else {
        fetchProducts()
      }
    }, 300) // 300ms debounce

    return () => clearTimeout(timer)
  }, [searchQuery, isVoiceSearchResult]) // Remove fetchProducts from deps to prevent re-runs

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        {/* Header */}
        <Header 
          onImageSearchClick={() => setShowImageSearch(true)} 
          onCartClick={() => setCartOpen(true)}
          onOrdersClick={() => setOrdersOpen(true)}
        />

        {/* Main Content */}
        <div className="flex h-[calc(100vh-64px)]">
          {/* Left Panel - Products */}
          <main className="flex-1 overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto">
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
            {/* Voice Assistant */}
            <VoiceAssistant realtimeSession={realtimeSession} />
            
            {/* Chat History with Input */}
            <ChatPanel realtimeSession={realtimeSession} />
          </aside>
        </div>

        {/* Image Search Modal */}
        {showImageSearch && (
          <ImageSearch onClose={() => setShowImageSearch(false)} />
        )}

        {/* Cart Panel Modal */}
        {isCartOpen && (
          <CartPanel onClose={() => setCartOpen(false)} />
        )}

        {/* Orders Panel Modal */}
        {isOrdersOpen && (
          <OrdersPanel onClose={() => setOrdersOpen(false)} />
        )}
      </div>
    </Router>
  )
}

export default App
