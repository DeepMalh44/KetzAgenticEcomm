import { useRef, useEffect, useState, FormEvent } from 'react'
import { Person24Regular, Bot24Regular, Send24Regular, Video24Regular, Eye24Regular } from '@fluentui/react-icons'
import { useAppStore, ChatMessage, DIYVideo } from '../store/appStore'
import { useRealtimeSession } from '../hooks/useRealtimeSession'

interface ChatPanelProps {
  realtimeSession: ReturnType<typeof useRealtimeSession>
}

export default function ChatPanel({ realtimeSession }: ChatPanelProps) {
  const { messages, diyVideos, clearDiyVideos } = useAppStore()
  const { sendTextMessage, isSpeaking } = realtimeSession
  const scrollRef = useRef<HTMLDivElement>(null)
  const [inputText, setInputText] = useState('')
  const [isSending, setIsSending] = useState(false)

  // Auto-scroll to bottom on new messages or DIY videos
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, diyVideos])

  // Handle form submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!inputText.trim() || isSending) return

    setIsSending(true)
    try {
      await sendTextMessage(inputText.trim())
      setInputText('')
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-200">
        <h3 className="font-semibold text-slate-800">Conversation</h3>
        <p className="text-xs text-slate-500">
          {messages.length} message{messages.length !== 1 ? 's' : ''} • Type or speak
        </p>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Bot24Regular className="w-8 h-8 text-slate-400" />
            </div>
            <p className="text-slate-500 text-sm">
              Start a conversation with Ketz, your home improvement assistant
            </p>
            <p className="text-slate-400 text-xs mt-2">
              Use the mic button above or type below
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}
        
        {/* Typing indicator when assistant is responding */}
        {isSpeaking && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-accent-100 text-accent-600">
              <Bot24Regular className="w-5 h-5" />
            </div>
            <div className="bg-slate-100 rounded-2xl rounded-tl-md px-4 py-2">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        
        {/* DIY Tutorial Videos Section */}
        {diyVideos && diyVideos.length > 0 && (
          <div className="mt-4 p-4 bg-gradient-to-r from-red-50 to-orange-50 rounded-xl border border-red-100">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Video24Regular className="w-5 h-5 text-red-600" />
                <h4 className="font-semibold text-slate-800">DIY Tutorial Videos</h4>
              </div>
              <button
                onClick={() => clearDiyVideos()}
                className="text-xs text-slate-500 hover:text-slate-700"
              >
                Dismiss
              </button>
            </div>
            <div className="space-y-3">
              {diyVideos.map((video) => (
                <DIYVideoCard key={video.video_id} video={video} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Chat Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-slate-200 bg-slate-50">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type a message..."
            disabled={isSending}
            className="flex-1 px-4 py-2 text-sm border border-slate-300 rounded-full focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isSending}
            className="p-2 bg-primary-500 text-white rounded-full hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send24Regular className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-slate-400 mt-2 text-center">
          Press Enter to send • Or use voice above
        </p>
      </form>
    </div>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-primary-100 text-primary-600'
            : 'bg-accent-100 text-accent-600'
        }`}
      >
        {isUser ? (
          <Person24Regular className="w-5 h-5" />
        ) : (
          <Bot24Regular className="w-5 h-5" />
        )}
      </div>

      {/* Content */}
      <div className={`flex-1 ${isUser ? 'text-right' : ''}`}>
        <div
          className={`inline-block px-4 py-2 rounded-2xl max-w-[80%] ${
            isUser
              ? 'bg-primary-500 text-white rounded-tr-md'
              : 'bg-slate-100 text-slate-800 rounded-tl-md'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Products mentioned */}
        {message.products && message.products.length > 0 && (
          <div className="mt-2 space-y-2">
            {message.products.slice(0, 3).map((product) => (
              <div
                key={product.id}
                className="inline-flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm"
              >
                <img
                  src={product.image_url}
                  alt={product.name}
                  className="w-10 h-10 object-cover rounded"
                />
                <div className="text-left">
                  <p className="font-medium text-slate-800 line-clamp-1">
                    {product.name}
                  </p>
                  <p className="text-slate-500">${product.price.toFixed(2)}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <p className="text-xs text-slate-400 mt-1">
          {formatTime(message.timestamp)}
        </p>
      </div>
    </div>
  )
}

function formatTime(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date)
}

function DIYVideoCard({ video }: { video: DIYVideo }) {
  return (
    <a
      href={video.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex gap-3 p-2 bg-white rounded-lg border border-slate-200 hover:border-red-300 hover:shadow-md transition-all group"
    >
      {/* Thumbnail */}
      <div className="relative flex-shrink-0">
        <img
          src={video.thumbnail_url}
          alt={video.title}
          className="w-32 h-20 object-cover rounded"
        />
        {/* Play button overlay */}
        <div className="absolute inset-0 flex items-center justify-center bg-black/30 group-hover:bg-black/40 transition-colors rounded">
          <div className="w-10 h-10 bg-red-600 rounded-full flex items-center justify-center">
            <svg className="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
        </div>
      </div>
      
      {/* Video Info */}
      <div className="flex-1 min-w-0">
        <h5 className="font-medium text-sm text-slate-800 line-clamp-2 group-hover:text-red-600 transition-colors">
          {video.title}
        </h5>
        <p className="text-xs text-slate-500 mt-1">{video.channel_name}</p>
        <div className="flex items-center gap-2 mt-1">
          <div className="flex items-center gap-1 text-xs text-slate-400">
            <Eye24Regular className="w-3 h-3" />
            <span>{video.view_count_formatted}</span>
          </div>
        </div>
      </div>
    </a>
  )
}
