import { create } from 'zustand'

export interface Product {
  id: string
  name: string
  description: string
  category: string
  subcategory: string
  brand: string
  sku: string
  price: number
  sale_price?: number
  rating: number
  review_count: number
  in_stock: boolean
  image_url: string
  featured?: boolean
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  products?: Product[]
}

export interface AppState {
  // Products
  products: Product[]
  selectedProduct: Product | null
  isLoading: boolean
  searchQuery: string
  selectedCategory: string | null
  
  // Voice
  isListening: boolean
  isSpeaking: boolean
  isConnected: boolean
  
  // Chat
  messages: ChatMessage[]
  
  // Actions
  setProducts: (products: Product[]) => void
  setSelectedProduct: (product: Product | null) => void
  setLoading: (loading: boolean) => void
  setSearchQuery: (query: string) => void
  setSelectedCategory: (category: string | null) => void
  setListening: (listening: boolean) => void
  setSpeaking: (speaking: boolean) => void
  setConnected: (connected: boolean) => void
  addMessage: (message: ChatMessage) => void
  clearMessages: () => void
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  products: [],
  selectedProduct: null,
  isLoading: false,
  searchQuery: '',
  selectedCategory: null,
  isListening: false,
  isSpeaking: false,
  isConnected: false,
  messages: [],
  
  // Actions
  setProducts: (products) => set({ products }),
  setSelectedProduct: (product) => set({ selectedProduct: product }),
  setLoading: (loading) => set({ isLoading: loading }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setSelectedCategory: (category) => set({ selectedCategory: category }),
  setListening: (listening) => set({ isListening: listening }),
  setSpeaking: (speaking) => set({ isSpeaking: speaking }),
  setConnected: (connected) => set({ isConnected: connected }),
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message] 
  })),
  clearMessages: () => set({ messages: [] }),
}))
