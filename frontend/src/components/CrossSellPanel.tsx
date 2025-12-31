import { useState } from 'react'
import { Star24Filled, Cart24Regular, Checkmark24Filled, Sparkle24Filled, Dismiss24Regular } from '@fluentui/react-icons'
import { Product, useAppStore } from '../store/appStore'

export default function CrossSellPanel() {
  const { crossSellData, clearCrossSellData, addToCart, cartItems, setSelectedProduct } = useAppStore()
  const [addedProductId, setAddedProductId] = useState<string | null>(null)

  if (!crossSellData || crossSellData.recommendations.length === 0) {
    return null
  }

  const handleAddToCart = (e: React.MouseEvent, product: Product) => {
    e.stopPropagation()
    addToCart(product, 1)
    setAddedProductId(product.id)
    setTimeout(() => setAddedProductId(null), 1500)
  }

  const isInCart = (productId: string) => {
    return cartItems.some(item => item.product.id === productId)
  }

  const contextTitle = crossSellData.context === 'cart' 
    ? 'Complete Your Project' 
    : 'You May Also Like'
  
  const contextSubtitle = crossSellData.context === 'cart'
    ? 'Based on items in your cart'
    : `Based on your search`

  return (
    <div className="mt-8 bg-gradient-to-r from-accent-50 via-white to-primary-50 rounded-xl p-4 sm:p-6 border border-accent-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-accent-500 rounded-full flex items-center justify-center">
            <Sparkle24Filled className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-800">{contextTitle}</h3>
            <p className="text-sm text-slate-500">{contextSubtitle}</p>
          </div>
        </div>
        <button 
          onClick={clearCrossSellData}
          className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors"
          aria-label="Dismiss recommendations"
        >
          <Dismiss24Regular className="w-5 h-5" />
        </button>
      </div>

      {/* Recommendations Grid - Responsive: stacked on mobile, horizontal scroll on small screens, grid on larger */}
      <div className="flex flex-col sm:flex-row sm:overflow-x-auto sm:gap-4 md:grid md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 md:gap-4 gap-3 pb-2">
        {crossSellData.recommendations.map((product) => (
          <div
            key={product.id}
            className="flex-shrink-0 w-full sm:w-48 md:w-auto bg-white rounded-lg shadow-sm border border-slate-100 overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => setSelectedProduct(product)}
          >
            {/* Product Image - smaller for cross-sell */}
            <div className="relative h-28 sm:h-32 bg-slate-50">
              <img
                src={product.image_url}
                alt={product.name}
                className="w-full h-full object-cover"
                loading="lazy"
              />
              {product.sale_price && (
                <span className="absolute top-2 left-2 px-1.5 py-0.5 bg-red-500 text-white text-[10px] font-bold rounded">
                  SALE
                </span>
              )}
            </div>

            {/* Product Info - compact */}
            <div className="p-3">
              {/* Brand */}
              <span className="text-[10px] font-medium text-primary-600 bg-primary-50 px-1.5 py-0.5 rounded">
                {product.brand}
              </span>

              {/* Name */}
              <h4 className="font-medium text-slate-800 text-sm mt-1 line-clamp-2 min-h-[2.5rem]">
                {product.name}
              </h4>

              {/* Rating */}
              <div className="flex items-center gap-1 mt-1">
                <Star24Filled className="w-3 h-3 text-amber-400" />
                <span className="text-xs font-medium text-slate-700">
                  {(product.rating ?? 0).toFixed(1)}
                </span>
              </div>

              {/* Price & Add to Cart */}
              <div className="flex items-center justify-between mt-2">
                <div className="flex flex-col">
                  <span className="text-base font-bold text-slate-800">
                    ${((product.sale_price || product.price) ?? 0).toFixed(2)}
                  </span>
                  {product.sale_price && (
                    <span className="text-xs text-slate-400 line-through">
                      ${(product.price ?? 0).toFixed(2)}
                    </span>
                  )}
                </div>

                <button
                  onClick={(e) => handleAddToCart(e, product)}
                  disabled={addedProductId === product.id}
                  className={`p-1.5 rounded-full transition-all ${
                    addedProductId === product.id
                      ? 'bg-green-500 text-white scale-110'
                      : isInCart(product.id)
                      ? 'bg-primary-100 text-primary-600'
                      : 'bg-primary-500 text-white hover:bg-primary-600'
                  }`}
                  title={isInCart(product.id) ? 'Already in cart' : 'Add to cart'}
                >
                  {addedProductId === product.id ? (
                    <Checkmark24Filled className="w-4 h-4" />
                  ) : (
                    <Cart24Regular className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Voice summary hint */}
      {crossSellData.summary && (
        <p className="text-xs text-slate-500 mt-3 italic">
          💡 {crossSellData.summary}
        </p>
      )}
    </div>
  )
}
