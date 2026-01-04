import { 
  Dismiss24Regular, 
  Box24Regular,
  ArrowCounterclockwise24Regular,
  Checkmark24Filled,
  Clock24Regular,
  VehicleTruck24Regular,
  Warning24Filled
} from '@fluentui/react-icons'
import { useAppStore, Order } from '../store/appStore'
import { useState, useEffect } from 'react'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

interface OrdersPanelProps {
  onClose: () => void
}

const statusConfig: Record<string, { icon: React.ReactNode; color: string; bgColor: string }> = {
  confirmed: { 
    icon: <Checkmark24Filled className="w-4 h-4" />, 
    color: 'text-green-700', 
    bgColor: 'bg-green-100' 
  },
  processing: { 
    icon: <Clock24Regular className="w-4 h-4" />, 
    color: 'text-blue-700', 
    bgColor: 'bg-blue-100' 
  },
  shipped: { 
    icon: <VehicleTruck24Regular className="w-4 h-4" />, 
    color: 'text-purple-700', 
    bgColor: 'bg-purple-100' 
  },
  delivered: { 
    icon: <Checkmark24Filled className="w-4 h-4" />, 
    color: 'text-green-700', 
    bgColor: 'bg-green-100' 
  },
  cancelled: { 
    icon: <Warning24Filled className="w-4 h-4" />, 
    color: 'text-red-700', 
    bgColor: 'bg-red-100' 
  },
  returned: { 
    icon: <ArrowCounterclockwise24Regular className="w-4 h-4" />, 
    color: 'text-orange-700', 
    bgColor: 'bg-orange-100' 
  },
}

export default function OrdersPanel({ onClose }: OrdersPanelProps) {
  const { orders, setOrders, orderFilter } = useAppStore()
  const [isLoading, setIsLoading] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
  const [isInitiatingReturn, setIsInitiatingReturn] = useState(false)
  const [returnMessage, setReturnMessage] = useState<string | null>(null)

  // Fetch orders from backend
  useEffect(() => {
    const fetchOrders = async () => {
      setIsLoading(true)
      try {
        const response = await fetch(`${BACKEND_URL}/api/v1/orders/?limit=50`)
        if (response.ok) {
          const data = await response.json()
          setOrders(data.orders || [])
        }
      } catch (error) {
        console.error('Failed to fetch orders:', error)
      } finally {
        setIsLoading(false)
      }
    }
    fetchOrders()
  }, [setOrders])

  // Filter orders if orderFilter is set
  const filteredOrders = orderFilter
    ? orders.filter(order => order.id.toLowerCase().includes(orderFilter.toLowerCase()))
    : orders

  const handleInitiateReturn = async (order: Order) => {
    setIsInitiatingReturn(true)
    setReturnMessage(null)
    
    try {
      // For demo purposes, we'll simulate a return initiation
      // In production, this would call the returns API
      const response = await fetch(`${BACKEND_URL}/api/v1/orders/${order.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: 'return_requested' })
      })
      
      if (response.ok) {
        setReturnMessage('Return request submitted successfully! Our team will contact you within 24 hours.')
        // Update local order status
        const updatedOrders = orders.map(o => 
          o.id === order.id ? { ...o, status: 'return_requested' } : o
        )
        setOrders(updatedOrders)
      } else {
        setReturnMessage('Unable to process return at this time. Please try again later.')
      }
    } catch {
      setReturnMessage('Unable to process return at this time. Please try again later.')
    } finally {
      setIsInitiatingReturn(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusDisplay = (status: string) => {
    const config = statusConfig[status] || statusConfig.processing
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.color} ${config.bgColor}`}>
        {config.icon}
        {status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
      </span>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <Box24Regular className="w-6 h-6 text-primary-600" />
            <h2 className="text-xl font-bold text-slate-800">My Orders</h2>
            <span className="px-2 py-0.5 bg-primary-100 text-primary-700 text-sm font-medium rounded-full">
              {filteredOrders.length} {orderFilter ? 'filtered' : 'orders'}
            </span>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <Dismiss24Regular className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
            </div>
          ) : filteredOrders.length === 0 ? (
            <div className="text-center py-12">
              <Box24Regular className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500 text-lg">{orderFilter ? 'No orders found matching filter' : 'No orders yet'}</p>
              <p className="text-slate-400 text-sm mt-1">{orderFilter ? `No orders match: ${orderFilter}` : 'Your order history will appear here'}</p>
            </div>
          ) : selectedOrder ? (
            // Order Detail View
            <div>
              <button 
                onClick={() => {
                  setSelectedOrder(null)
                  setReturnMessage(null)
                }}
                className="text-primary-600 hover:text-primary-700 font-medium mb-4 flex items-center gap-1"
              >
                ← Back to orders
              </button>
              
              <div className="bg-slate-50 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-sm text-slate-500">Order ID</p>
                    <p className="font-mono text-sm">{selectedOrder.id.slice(0, 8)}...</p>
                  </div>
                  {getStatusDisplay(selectedOrder.status)}
                </div>
                
                <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
                  <div>
                    <p className="text-slate-500">Order Date</p>
                    <p className="font-medium">{formatDate(selectedOrder.created_at)}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Estimated Delivery</p>
                    <p className="font-medium">{selectedOrder.estimated_delivery || '3-5 business days'}</p>
                  </div>
                </div>
                
                <div className="border-t pt-4">
                  <h4 className="font-semibold mb-3">Items</h4>
                  <div className="space-y-3">
                    {selectedOrder.items.map((item, idx) => (
                      <div key={idx} className="flex justify-between items-center">
                        <div>
                          <p className="font-medium">{item.product_name}</p>
                          <p className="text-sm text-slate-500">Qty: {item.quantity} × ${item.unit_price.toFixed(2)}</p>
                        </div>
                        <p className="font-medium">${item.total_price.toFixed(2)}</p>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="border-t mt-4 pt-4 space-y-2">
                  <div className="flex justify-between text-slate-600">
                    <span>Subtotal</span>
                    <span>${selectedOrder.subtotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Tax</span>
                    <span>${selectedOrder.tax.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between font-bold text-lg pt-2 border-t">
                    <span>Total</span>
                    <span>${selectedOrder.total.toFixed(2)}</span>
                  </div>
                </div>
                
                {returnMessage && (
                  <div className={`mt-4 p-3 rounded-lg text-sm ${
                    returnMessage.includes('successfully') 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {returnMessage}
                  </div>
                )}
                
                {/* Return Button */}
                {['confirmed', 'delivered'].includes(selectedOrder.status) && (
                  <button 
                    onClick={() => handleInitiateReturn(selectedOrder)}
                    disabled={isInitiatingReturn}
                    className="mt-4 w-full py-3 border border-orange-400 text-orange-600 hover:bg-orange-50 rounded-xl font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <ArrowCounterclockwise24Regular />
                    {isInitiatingReturn ? 'Processing...' : 'Request Return'}
                  </button>
                )}
              </div>
            </div>
          ) : (
            // Orders List View
            <div className="space-y-4">
              {filteredOrders.map((order) => (
                <div 
                  key={order.id}
                  onClick={() => setSelectedOrder(order)}
                  className="p-4 bg-slate-50 rounded-xl hover:bg-slate-100 cursor-pointer transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                        <Box24Regular className="w-5 h-5 text-primary-600" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-800">
                          Order #{order.id.slice(0, 8)}
                        </p>
                        <p className="text-sm text-slate-500">{formatDate(order.created_at)}</p>
                      </div>
                    </div>
                    {getStatusDisplay(order.status)}
                  </div>
                  
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-200">
                    <p className="text-sm text-slate-500">
                      {order.items.length} item{order.items.length > 1 ? 's' : ''}
                    </p>
                    <p className="font-semibold text-slate-800">${order.total.toFixed(2)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
