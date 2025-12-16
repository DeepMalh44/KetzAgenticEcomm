import { useRef, useState, useCallback } from 'react'
import { 
  Dismiss24Regular, 
  Image24Regular, 
  ArrowUpload24Regular,
  Search24Regular 
} from '@fluentui/react-icons'
import { useAppStore } from '../store/appStore'

interface ImageSearchProps {
  onClose: () => void
}

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

export default function ImageSearch({ onClose }: ImageSearchProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { setProducts, addMessage } = useAppStore()

  // Handle file selection
  const handleFileSelect = useCallback(async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file')
      return
    }

    // Preview
    const reader = new FileReader()
    reader.onload = (e) => {
      setPreviewUrl(e.target?.result as string)
    }
    reader.readAsDataURL(file)
    setError(null)

    // Upload and search
    await searchByImage(file)
  }, [])

  // Search by uploaded image
  const searchByImage = async (file: File) => {
    setIsSearching(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${BACKEND_URL}/api/v1/images/search`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Search failed')
      }

      const result = await response.json()
      
      if (result.products && result.products.length > 0) {
        setProducts(result.products, true)  // Set isVoiceSearch flag to prevent auto-refresh
        addMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `I found ${result.products.length} products similar to your image. The best match is "${result.products[0].name}".`,
          timestamp: new Date(),
          products: result.products
        })
        onClose()
      } else {
        setError('No similar products found. Try a different image.')
      }
    } catch (err) {
      console.error('Image search error:', err)
      setError('Failed to search. Please try again.')
    } finally {
      setIsSearching(false)
    }
  }

  // Drag and drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileSelect(file)
    }
  }, [handleFileSelect])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <Image24Regular className="text-primary-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-800">Image Search</h2>
              <p className="text-sm text-slate-500">Find products by uploading a photo</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <Dismiss24Regular className="text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Dropzone */}
          <div
            className={`dropzone relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${
              isDragging
                ? 'drag-over border-primary-500 bg-primary-50'
                : 'border-slate-300 hover:border-primary-400'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) handleFileSelect(file)
              }}
            />

            {previewUrl ? (
              // Preview
              <div className="space-y-4">
                <img
                  src={previewUrl}
                  alt="Preview"
                  className="w-48 h-48 object-cover rounded-lg mx-auto shadow-md"
                />
                {isSearching ? (
                  <div className="flex items-center justify-center gap-2 text-primary-600">
                    <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    <span className="font-medium">Searching for similar products...</span>
                  </div>
                ) : (
                  <button
                    className="text-sm text-slate-500 hover:text-primary-600"
                    onClick={(e) => {
                      e.stopPropagation()
                      setPreviewUrl(null)
                    }}
                  >
                    Choose a different image
                  </button>
                )}
              </div>
            ) : (
              // Empty state
              <>
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <ArrowUpload24Regular className="w-8 h-8 text-slate-400" />
                </div>
                <h3 className="text-lg font-medium text-slate-700 mb-2">
                  Drop an image here
                </h3>
                <p className="text-slate-500 mb-4">
                  or click to browse your files
                </p>
                <p className="text-xs text-slate-400">
                  Supports JPG, PNG, WEBP up to 10MB
                </p>
              </>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Tips */}
          <div className="mt-6 p-4 bg-slate-50 rounded-lg">
            <h4 className="text-sm font-medium text-slate-700 mb-2">Tips for best results:</h4>
            <ul className="text-sm text-slate-500 space-y-1">
              <li>• Use a clear, well-lit photo of the product</li>
              <li>• Try to capture the whole item in the frame</li>
              <li>• Products with similar colors and shapes work best</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-slate-600 hover:text-slate-800 font-medium"
          >
            Cancel
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isSearching}
            className="flex items-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Search24Regular className="w-5 h-5" />
            <span>Search by Image</span>
          </button>
        </div>
      </div>
    </div>
  )
}
