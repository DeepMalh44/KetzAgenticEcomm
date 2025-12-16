/**
 * Voice Assistant Component
 * Simplified version using the shared useRealtimeSession hook
 */
import { Mic24Filled, Stop24Filled } from '@fluentui/react-icons'
import { useRealtimeSession } from '../hooks/useRealtimeSession'

interface VoiceAssistantProps {
  realtimeSession: ReturnType<typeof useRealtimeSession>
}

export default function VoiceAssistant({ realtimeSession }: VoiceAssistantProps) {
  const {
    isConnected,
    isListening,
    isSpeaking,
    transcript,
    assistantText,
    toggleVoiceSession,
  } = realtimeSession

  return (
    <div className="p-6 border-b border-slate-200 bg-gradient-to-br from-primary-50 to-slate-50">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-slate-400'}`} />
          <span className="text-sm text-slate-600">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        {isSpeaking && (
          <span className="text-sm text-primary-600 font-medium animate-pulse">
            Ketz is speaking...
          </span>
        )}
      </div>

      <div className="flex items-center justify-center gap-1 h-12 mb-4">
        {isListening ? (
          [...Array(5)].map((_, i) => (
            <div key={i} className="w-2 bg-primary-500 rounded-full animate-pulse"
              style={{ height: `${20 + Math.random() * 60}%`, animationDelay: `${i * 0.1}s` }} />
          ))
        ) : isSpeaking ? (
          [...Array(5)].map((_, i) => (
            <div key={i} className="w-2 bg-accent-500 rounded-full animate-pulse"
              style={{ height: `${30 + Math.random() * 50}%`, animationDelay: `${i * 0.1}s` }} />
          ))
        ) : (
          <span className="text-slate-400 text-sm">Click the mic to start talking</span>
        )}
      </div>

      <div className="flex justify-center">
        <button
          onClick={toggleVoiceSession}
          className={`relative p-6 rounded-full transition-all ${
            isListening
              ? 'bg-red-500 hover:bg-red-600 shadow-lg shadow-red-200'
              : 'bg-primary-500 hover:bg-primary-600 shadow-lg shadow-primary-200'
          }`}
        >
          {isListening && <span className="absolute inset-0 rounded-full bg-red-500 pulse-ring" />}
          {isListening ? (
            <Stop24Filled className="w-8 h-8 text-white relative z-10" />
          ) : (
            <Mic24Filled className="w-8 h-8 text-white relative z-10" />
          )}
        </button>
      </div>

      {transcript && (
        <div className="mt-4 p-3 bg-white rounded-lg border border-slate-200">
          <p className="text-sm text-slate-600"><span className="font-medium">You:</span> {transcript}</p>
        </div>
      )}

      {assistantText && (
        <div className="mt-2 p-3 bg-primary-50 rounded-lg border border-primary-100">
          <p className="text-sm text-primary-800"><span className="font-medium">Ketz:</span> {assistantText}</p>
        </div>
      )}
    </div>
  )
}
