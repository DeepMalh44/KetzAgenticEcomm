import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import CartPanel from './components/CartPanel'
import OrdersPanel from './components/OrdersPanel'
import HomePage from './pages/HomePage'
import AgenticSearchPage from './pages/AgenticSearchPage'
import { useAppStore } from './store/appStore'
import { useRealtimeSession } from './hooks/useRealtimeSession'

function App() {
  const [showImageSearch, setShowImageSearch] = useState(false)
  const { 
    isCartOpen,
    setCartOpen,
    isOrdersOpen,
    setOrdersOpen,
  } = useAppStore()

  // Shared realtime session for voice and chat
  const realtimeSession = useRealtimeSession()

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        {/* Header */}
        <Header 
          onImageSearchClick={() => setShowImageSearch(true)} 
          onCartClick={() => setCartOpen(true)}
          onOrdersClick={() => setOrdersOpen(true)}
        />

        {/* Routes */}
        <Routes>
          <Route 
            path="/" 
            element={
              <HomePage 
                realtimeSession={realtimeSession}
                showImageSearch={showImageSearch}
                setShowImageSearch={setShowImageSearch}
              />
            } 
          />
          <Route 
            path="/agentic" 
            element={
              <AgenticSearchPage 
                realtimeSession={realtimeSession}
                showImageSearch={showImageSearch}
                setShowImageSearch={setShowImageSearch}
              />
            } 
          />
        </Routes>

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
