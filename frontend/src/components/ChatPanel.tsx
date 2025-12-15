import { useRef, useEffect } from 'react'
import { Person24Regular, Bot24Regular } from '@fluentui/react-icons'
import { useAppStore, ChatMessage } from '../store/appStore'

export default function ChatPanel() {
  const { messages } = useAppStore()
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-200">
        <h3 className="font-semibold text-slate-800">Conversation</h3>
        <p className="text-xs text-slate-500">
          {messages.length} message{messages.length !== 1 ? 's' : ''}
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
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}
      </div>
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
