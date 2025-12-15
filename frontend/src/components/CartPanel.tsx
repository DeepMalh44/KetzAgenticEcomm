import { 
  Dismiss24Regular, 
  Add24Regular, 
  Subtract24Regular,
  Delete24Regular,
  Cart24Regular,
  Checkmark24Regular
} from '@fluentui/react-icons'
import { useAppStore, Order } from '../store/appStore'
import { useState } from 'react'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

interface CartPanelProps {
  onClose: () => void
}

export default function CartPanel({ onClose }: CartPanelProps) {
  const { 
    cartItems, 
    removeFromCart, 
    updateCartQuantity, 
    clearCart, 
    getCartTotal,
    addOrder,
    setOrdersOpen,
    setCartOpen
  } = useAppStore()
  
  const [isCheckingOut, setIsCheckingOut] = useState(false)
  const [checkoutSuccess, setCheckoutSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const subtotal = getCartTotal()
  const tax = subtotal * 0.0825
  const total = subtotal + tax

  const handleCheckout = async () => {
    if (cartItems.length === 0) return
    
    setIsCheckingOut(true)
    setError(null)
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/orders/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          items: cartItems.map(item => ({
            product_id: item.product.id,
            quantity: item.quantity
          })),
          customer_id: 'guest-user',
          delivery_address: '123 Main St, Anytown, USA'
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to create order')
      }
      
      const order: Order = await response.json()
      addOrder(order)
      clearCart()
      setCheckoutSuccess(true)
      
      // Show success for 2 seconds then close
      setTimeout(() => {
        setCheckoutSuccess(false)
        setCartOpen(false)
        setOrdersOpen(true)
      }, 2000)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Checkout failed')
    } finally {
      setIsCheckingOut(false)
    }
  }

  if (checkoutSuccess) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-8 text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Checkmark24Regular className="w-10 h-10 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-slate-800 mb-2">Order Placed!</h2>
          <p className="text-slate-600">Your order has been successfully placed. Check your orders for details.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <Cart24Regular className="w-6 h-6 text-primary-600" />
            <h2 className="text-xl font-bold text-slate-800">Shopping Cart</h2>
            <span className="px-2 py-0.5 bg-primary-100 text-primary-700 text-sm font-medium rounded-full">
              {cartItems.length} items
            </span>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <Dismiss24Regular className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Cart Items */}
        <div className="flex-1 overflow-y-auto p-6">
          {cartItems.length === 0 ? (
            <div className="text-center py-12">
              <Cart24Regular className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500 text-lg">Your cart is empty</p>
              <p className="text-slate-400 text-sm mt-1">Add some products to get started</p>
            </div>
          ) : (
            <div className="space-y-4">
              {cartItems.map((item) => (
                <div 
                  key={item.product.id}
                  className="flex gap-4 p-4 bg-slate-50 rounded-xl"
                >
                  <img 
                    src={item.product.image_url}
                    alt={item.product.name}
                    className="w-20 h-20 object-cover rounded-lg"
                  />
                  <div className="flex-1">
                    <h3 className="font-medium text-slate-800 line-clamp-1">
                      {item.product.name}
                    </h3>
                    <p className="text-sm text-slate-500">{item.product.brand}</p>
                    <p className="font-semibold text-primary-600 mt-1">
                      ${(item.product.sale_price || item.product.price).toFixed(2)}
                    </p>
                  </div>
                  <div className="flex flex-col items-end justify-between">
                    <button 
                      onClick={() => removeFromCart(item.product.id)}
                      className="p-1 hover:bg-red-100 rounded text-red-500 transition-colors"
                    >
                      <Delete24Regular className="w-5 h-5" />
                    </button>
                    <div className="flex items-center gap-2 bg-white rounded-lg border">
                      <button 
                        onClick={() => updateCartQuantity(item.product.id, item.quantity - 1)}
                        className="p-1.5 hover:bg-slate-100 rounded-l-lg transition-colors"
                      >
                        <Subtract24Regular className="w-4 h-4" />
                      </button>
                      <span className="w-8 text-center font-medium">{item.quantity}</span>
                      <button 
                        onClick={() => updateCartQuantity(item.product.id, item.quantity + 1)}
                        className="p-1.5 hover:bg-slate-100 rounded-r-lg transition-colors"
                      >
                        <Add24Regular className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Summary & Checkout */}
        {cartItems.length > 0 && (
          <div className="border-t p-6 space-y-4 bg-slate-50">
            {error && (
              <div className="p-3 bg-red-100 text-red-700 rounded-lg text-sm">
                {error}
              </div>
            )}
            
            <div className="space-y-2">
              <div className="flex justify-between text-slate-600">
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Tax (8.25%)</span>
                <span>${tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-lg font-bold text-slate-800 pt-2 border-t">
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>
            </div>
            
            <div className="flex gap-3">
              <button 
                onClick={clearCart}
                className="flex-1 py-3 border border-slate-300 rounded-xl font-medium text-slate-700 hover:bg-slate-100 transition-colors"
              >
                Clear Cart
              </button>
              <button 
                onClick={handleCheckout}
                disabled={isCheckingOut}
                className="flex-1 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCheckingOut ? 'Processing...' : 'Checkout'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
