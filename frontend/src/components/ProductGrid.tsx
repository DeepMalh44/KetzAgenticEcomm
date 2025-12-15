import { Star24Filled, Cart24Regular, Eye24Regular, Checkmark24Filled } from '@fluentui/react-icons'
import { Product, useAppStore } from '../store/appStore'
import { useState } from 'react'

interface ProductGridProps {
  products: Product[]
  isLoading: boolean
}

export default function ProductGrid({ products, isLoading }: ProductGridProps) {
  const { setSelectedProduct, addToCart, cartItems } = useAppStore()
  const [addedProductId, setAddedProductId] = useState<string | null>(null)

  const handleAddToCart = (e: React.MouseEvent, product: Product) => {
    e.stopPropagation()
    addToCart(product, 1)
    setAddedProductId(product.id)
    // Reset the animation after 1.5 seconds
    setTimeout(() => setAddedProductId(null), 1500)
  }

  const isInCart = (productId: string) => {
    return cartItems.some(item => item.product.id === productId)
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="bg-slate-200 rounded-xl h-48 mb-4" />
            <div className="bg-slate-200 h-4 rounded w-3/4 mb-2" />
            <div className="bg-slate-200 h-4 rounded w-1/2" />
          </div>
        ))}
      </div>
    )
  }

  if (products.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="w-24 h-24 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Eye24Regular className="w-12 h-12 text-slate-400" />
        </div>
        <h3 className="text-xl font-semibold text-slate-700 mb-2">No products found</h3>
        <p className="text-slate-500">
          Try searching for something like "drill", "paint", or "lumber"
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {products.map((product) => (
        <div
          key={product.id}
          className="product-card bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden cursor-pointer"
          onClick={() => setSelectedProduct(product)}
        >
          {/* Product Image */}
          <div className="relative h-48 bg-slate-50">
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-cover"
              loading="lazy"
            />
            {product.sale_price && (
              <span className="absolute top-3 left-3 px-2 py-1 bg-red-500 text-white text-xs font-bold rounded">
                SALE
              </span>
            )}
            {product.featured && (
              <span className="absolute top-3 right-3 px-2 py-1 bg-accent-500 text-white text-xs font-bold rounded">
                FEATURED
              </span>
            )}
          </div>

          {/* Product Info */}
          <div className="p-4">
            {/* Brand & Category */}
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium text-primary-600 bg-primary-50 px-2 py-0.5 rounded">
                {product.brand}
              </span>
              <span className="text-xs text-slate-500">
                {product.category.replace('_', ' ')}
              </span>
            </div>

            {/* Name */}
            <h3 className="font-semibold text-slate-800 mb-2 line-clamp-2">
              {product.name}
            </h3>

            {/* Rating */}
            <div className="flex items-center gap-1 mb-3">
              <Star24Filled className="w-4 h-4 text-amber-400" />
              <span className="text-sm font-medium text-slate-700">
                {product.rating.toFixed(1)}
              </span>
              <span className="text-xs text-slate-400">
                ({product.review_count} reviews)
              </span>
            </div>

            {/* Price */}
            <div className="flex items-center justify-between">
              <div className="flex items-baseline gap-2">
                <span className="text-xl font-bold text-slate-800">
                  ${(product.sale_price || product.price).toFixed(2)}
                </span>
                {product.sale_price && (
                  <span className="text-sm text-slate-400 line-through">
                    ${product.price.toFixed(2)}
                  </span>
                )}
              </div>
              
              <button 
                className={`p-2 rounded-lg transition-all duration-300 ${
                  addedProductId === product.id
                    ? 'bg-green-500 scale-110'
                    : isInCart(product.id)
                    ? 'bg-green-500 hover:bg-green-600'
                    : 'bg-primary-500 hover:bg-primary-600'
                } text-white`}
                onClick={(e) => handleAddToCart(e, product)}
                disabled={!product.in_stock}
              >
                {addedProductId === product.id ? (
                  <Checkmark24Filled className="w-5 h-5" />
                ) : (
                  <Cart24Regular className="w-5 h-5" />
                )}
              </button>
            </div>

            {/* Stock Status */}
            <div className="mt-3">
              {product.in_stock ? (
                <span className="text-xs text-green-600 font-medium">✓ In Stock</span>
              ) : (
                <span className="text-xs text-red-600 font-medium">Out of Stock</span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
