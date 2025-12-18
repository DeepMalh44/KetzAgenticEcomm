import { 
  Home24Regular, 
  Search24Regular,
  Image24Regular,
  Cart24Regular,
  Box24Regular,
  BrainCircuit24Regular 
} from '@fluentui/react-icons'
import { NavLink } from 'react-router-dom'
import { useAppStore } from '../store/appStore'

interface HeaderProps {
  onImageSearchClick: () => void
  onCartClick: () => void
  onOrdersClick: () => void
}

export default function Header({ onImageSearchClick, onCartClick, onOrdersClick }: HeaderProps) {
  const { cartItems, orders } = useAppStore()
  
  const cartItemCount = cartItems.reduce((sum, item) => sum + item.quantity, 0)

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shadow-sm">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center">
          <Home24Regular className="text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-slate-800">KetzAgenticEcomm</h1>
          <p className="text-xs text-slate-500">Home Improvement Voice Assistant</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex items-center gap-2">
        {/* Page Navigation Links */}
        <NavLink
          to="/"
          className={({ isActive }) =>
            `flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              isActive 
                ? 'bg-blue-100 text-blue-700' 
                : 'hover:bg-slate-100 text-slate-600 hover:text-primary-600'
            }`
          }
        >
          <Search24Regular />
          <span className="text-sm font-medium">Semantic</span>
        </NavLink>

        <NavLink
          to="/agentic"
          className={({ isActive }) =>
            `flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              isActive 
                ? 'bg-purple-100 text-purple-700' 
                : 'hover:bg-slate-100 text-slate-600 hover:text-purple-600'
            }`
          }
        >
          <BrainCircuit24Regular />
          <span className="text-sm font-medium">Agentic</span>
        </NavLink>

        <div className="w-px h-6 bg-slate-200 mx-2" />

        <button
          onClick={onImageSearchClick}
          className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-slate-100 transition-colors text-slate-600 hover:text-primary-600"
        >
          <Image24Regular />
          <span className="text-sm font-medium">Image Search</span>
        </button>

        <div className="w-px h-6 bg-slate-200 mx-2" />

        <button 
          onClick={onOrdersClick}
          className="relative p-2 rounded-lg hover:bg-slate-100 transition-colors text-slate-600 hover:text-primary-600"
        >
          <Box24Regular />
          {orders.length > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-blue-500 rounded-full text-xs text-white flex items-center justify-center font-medium">
              {orders.length > 9 ? '9+' : orders.length}
            </span>
          )}
        </button>

        <button 
          onClick={onCartClick}
          className="relative p-2 rounded-lg hover:bg-slate-100 transition-colors text-slate-600 hover:text-primary-600"
        >
          <Cart24Regular />
          {cartItemCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-accent-500 rounded-full text-xs text-white flex items-center justify-center font-medium">
              {cartItemCount > 9 ? '9+' : cartItemCount}
            </span>
          )}
        </button>
      </nav>
    </header>
  )
}
