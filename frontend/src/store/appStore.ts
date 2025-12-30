import { create } from 'zustand'
import { persist } from 'zustand/middleware'

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

export interface CartItem {
  product: Product
  quantity: number
}

export interface OrderItem {
  product_id: string
  product_name: string
  quantity: number
  unit_price: number
  total_price: number
}

export interface Order {
  id: string
  customer_id?: string
  items: OrderItem[]
  subtotal: number
  tax: number
  total: number
  status: string
  delivery_address?: string
  estimated_delivery?: string
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  products?: Product[]
  diyVideos?: DIYVideo[]
}

export interface DIYVideo {
  video_id: string
  title: string
  url: string
  thumbnail_url: string
  view_count: number
  view_count_formatted: string
  channel_name: string
  published_date: string
}

export type SearchMode = 'semantic' | 'agentic'

export interface AppState {
  // Products
  products: Product[]
  selectedProduct: Product | null
  isLoading: boolean
  searchQuery: string
  selectedCategory: string | null
  isVoiceSearchResult: boolean  // Flag to prevent auto-refresh overwriting voice/image search results
  searchMode: SearchMode  // Which search endpoint to use for voice/typed search
  
  // DIY Videos
  diyVideos: DIYVideo[]
  
  // Cart
  cartItems: CartItem[]
  isCartOpen: boolean
  
  // Orders
  orders: Order[]
  isOrdersOpen: boolean
  
  // Voice
  isListening: boolean
  isSpeaking: boolean
  isConnected: boolean
  
  // Chat
  messages: ChatMessage[]
  
  // Product Actions
  setProducts: (products: Product[], isVoiceSearch?: boolean) => void
  setSelectedProduct: (product: Product | null) => void
  setLoading: (loading: boolean) => void
  setSearchQuery: (query: string) => void
  setSelectedCategory: (category: string | null) => void
  clearVoiceSearchFlag: () => void
  setSearchMode: (mode: SearchMode) => void
  
  // DIY Video Actions
  setDiyVideos: (videos: DIYVideo[]) => void
  clearDiyVideos: () => void
  
  // Cart Actions
  addToCart: (product: Product, quantity?: number) => void
  removeFromCart: (productId: string) => void
  updateCartQuantity: (productId: string, quantity: number) => void
  clearCart: () => void
  setCartOpen: (open: boolean) => void
  getCartTotal: () => number
  getCartItemCount: () => number
  
  // Order Actions
  setOrders: (orders: Order[]) => void
  addOrder: (order: Order) => void
  setOrdersOpen: (open: boolean) => void
  
  // Voice Actions
  setListening: (listening: boolean) => void
  setSpeaking: (speaking: boolean) => void
  setConnected: (connected: boolean) => void
  
  // Chat Actions
  addMessage: (message: ChatMessage) => void
  clearMessages: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      products: [],
      selectedProduct: null,
      isLoading: false,
      searchQuery: '',
      selectedCategory: null,
      isVoiceSearchResult: false,
      searchMode: 'semantic',
      
      // DIY Videos state
      diyVideos: [],
      
      // Cart state
      cartItems: [],
      isCartOpen: false,
      
      // Orders state
      orders: [],
      isOrdersOpen: false,
      
      // Voice state
      isListening: false,
      isSpeaking: false,
      isConnected: false,
      
      // Chat state
      messages: [],
      
      // Product Actions
      setProducts: (products, isVoiceSearch = false) => set({ products, isVoiceSearchResult: isVoiceSearch }),
      setSelectedProduct: (product) => set({ selectedProduct: product }),
      setLoading: (loading) => set({ isLoading: loading }),
      setSearchQuery: (query) => set({ searchQuery: query, isVoiceSearchResult: false }),  // Clear flag when user types search
      setSelectedCategory: (category) => set({ selectedCategory: category }),
      clearVoiceSearchFlag: () => set({ isVoiceSearchResult: false }),
      setSearchMode: (mode) => set({ searchMode: mode }),
      
      // DIY Video Actions
      setDiyVideos: (videos) => set({ diyVideos: videos }),
      clearDiyVideos: () => set({ diyVideos: [] }),
      
      // Cart Actions
      addToCart: (product, quantity = 1) => set((state) => {
        const existingItem = state.cartItems.find(item => item.product.id === product.id)
        if (existingItem) {
          return {
            cartItems: state.cartItems.map(item =>
              item.product.id === product.id
                ? { ...item, quantity: item.quantity + quantity }
                : item
            )
          }
        }
        return { cartItems: [...state.cartItems, { product, quantity }] }
      }),
      
      removeFromCart: (productId) => set((state) => ({
        cartItems: state.cartItems.filter(item => item.product.id !== productId)
      })),
      
      updateCartQuantity: (productId, quantity) => set((state) => {
        if (quantity <= 0) {
          return { cartItems: state.cartItems.filter(item => item.product.id !== productId) }
        }
        return {
          cartItems: state.cartItems.map(item =>
            item.product.id === productId ? { ...item, quantity } : item
          )
        }
      }),
      
      clearCart: () => set({ cartItems: [] }),
      
      setCartOpen: (open) => set({ isCartOpen: open }),
      
      getCartTotal: () => {
        const state = get()
        return state.cartItems.reduce((total, item) => {
          const price = item.product.sale_price || item.product.price
          return total + (price * item.quantity)
        }, 0)
      },
      
      getCartItemCount: () => {
        const state = get()
        return state.cartItems.reduce((count, item) => count + item.quantity, 0)
      },
      
      // Order Actions
      setOrders: (orders) => set({ orders }),
      addOrder: (order) => set((state) => ({ orders: [order, ...state.orders] })),
      setOrdersOpen: (open) => set({ isOrdersOpen: open }),
      
      // Voice Actions
      setListening: (listening) => set({ isListening: listening }),
      setSpeaking: (speaking) => set({ isSpeaking: speaking }),
      setConnected: (connected) => set({ isConnected: connected }),
      
      // Chat Actions
      addMessage: (message) => set((state) => ({ 
        messages: [...state.messages, message] 
      })),
      clearMessages: () => set({ messages: [] }),
    }),
    {
      name: 'ketz-ecomm-storage',
      partialize: (state) => ({ 
        cartItems: state.cartItems,
        orders: state.orders 
      }),
    }
  )
)
