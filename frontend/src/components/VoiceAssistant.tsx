/**
 * Voice Assistant Component
 * Based on Azure-Samples/art-voice-agent-accelerator patterns
 * Uses 24kHz PCM16 audio format as expected by GPT-4o Realtime
 */
import { useEffect, useRef, useCallback, useState } from 'react'
import { Mic24Filled, Stop24Filled } from '@fluentui/react-icons'
import { useAppStore } from '../store/appStore'

const BACKEND_WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

// AudioWorklet source code for smooth PCM streaming playback
const WORKLET_SOURCE = `
  class PcmSink extends AudioWorkletProcessor {
    constructor() {
      super();
      this.queue = [];
      this.readIndex = 0;
      this.port.onmessage = (e) => {
        if (e.data?.type === 'push') {
          this.queue.push(e.data.payload);
        } else if (e.data?.type === 'clear') {
          this.queue = [];
          this.readIndex = 0;
        }
      };
    }
    process(inputs, outputs) {
      const out = outputs[0][0];
      let i = 0;
      while (i < out.length) {
        if (this.queue.length === 0) {
          for (; i < out.length; i++) out[i] = 0;
          break;
        }
        const chunk = this.queue[0];
        const remain = chunk.length - this.readIndex;
        const toCopy = Math.min(remain, out.length - i);
        out.set(chunk.subarray(this.readIndex, this.readIndex + toCopy), i);
        i += toCopy;
        this.readIndex += toCopy;
        if (this.readIndex >= chunk.length) {
          this.queue.shift();
          this.readIndex = 0;
        }
      }
      return true;
    }
  }
  registerProcessor('pcm-sink', PcmSink);
`;

export default function VoiceAssistant() {
  const { 
    isListening, 
    isSpeaking, 
    isConnected,
    setListening, 
    setSpeaking, 
    setConnected,
    addMessage,
    setProducts,
  } = useAppStore()
  
  // WebSocket and audio refs
  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  
  // Playback refs (AudioWorklet-based)
  const playbackContextRef = useRef<AudioContext | null>(null)
  const pcmSinkRef = useRef<AudioWorkletNode | null>(null)
  
  // State
  const [transcript, setTranscript] = useState('')
  const [assistantText, setAssistantText] = useState('')
  const assistantTextRef = useRef('')
  const isActiveRef = useRef(false)
  const audioChunkCount = useRef(0)

  useEffect(() => {
    assistantTextRef.current = assistantText
  }, [assistantText])

  // Fetch full product details from the API
  const fetchFullProducts = useCallback(async (partialProducts: Array<{ id: string; name: string }>) => {
    try {
      // Get product IDs and fetch full details
      const productIds = partialProducts.map(p => p.id)
      console.log('🔍 Fetching full product details for:', productIds)
      
      // Fetch products by searching for each (or use a batch endpoint if available)
      const response = await fetch(`${BACKEND_URL}/api/v1/products/?limit=20`)
      if (response.ok) {
        const data = await response.json()
        // Filter to only the products that match the IDs from the voice search
        const matchedProducts = data.products?.filter((p: any) => 
          productIds.includes(p.id)
        ) || []
        
        if (matchedProducts.length > 0) {
          setProducts(matchedProducts)
          console.log('✅ Updated products in store:', matchedProducts.length)
        } else {
          // If no exact match, just use search with the first product name
          const searchResponse = await fetch(
            `${BACKEND_URL}/api/v1/products/search?query=${encodeURIComponent(partialProducts[0]?.name || '')}&limit=10`
          )
          if (searchResponse.ok) {
            const searchData = await searchResponse.json()
            if (searchData.products?.length > 0) {
              setProducts(searchData.products)
              console.log('✅ Updated products via search:', searchData.products.length)
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch full products:', error)
    }
  }, [setProducts])

  // Initialize AudioWorklet playback system
  const initPlayback = useCallback(async () => {
    if (playbackContextRef.current) return
    
    try {
      const ctx = new AudioContext({ sampleRate: 24000 })
      if (ctx.state === 'suspended') await ctx.resume()
      
      // Load worklet
      const blob = new Blob([WORKLET_SOURCE], { type: 'text/javascript' })
      await ctx.audioWorklet.addModule(URL.createObjectURL(blob))
      
      // Create sink node
      const sink = new AudioWorkletNode(ctx, 'pcm-sink', {
        numberOfInputs: 0,
        numberOfOutputs: 1,
        outputChannelCount: [1]
      })
      sink.connect(ctx.destination)
      
      playbackContextRef.current = ctx
      pcmSinkRef.current = sink
      console.log('🔊 AudioWorklet playback initialized')
    } catch (e) {
      console.error('❌ Playback init failed:', e)
    }
  }, [])

  // Play audio via AudioWorklet (smooth streaming)
  const playAudio = useCallback((base64Audio: string) => {
    try {
      if (!pcmSinkRef.current) {
        console.warn('⚠️ Playback not initialized')
        return
      }
      
      // Decode base64 -> Int16 -> Float32
      const binaryString = atob(base64Audio)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      
      const int16 = new Int16Array(bytes.buffer)
      const float32 = new Float32Array(int16.length)
      for (let i = 0; i < int16.length; i++) {
        float32[i] = int16[i] / 0x8000
      }
      
      // Push to worklet queue
      pcmSinkRef.current.port.postMessage({ type: 'push', payload: float32 })
      setSpeaking(true)
    } catch (e) {
      console.error('Audio playback error:', e)
    }
  }, [setSpeaking])

  // Handle server messages
  const handleServerMessage = useCallback((data: any) => {
    const type = data.type || 'unknown'
    if (type !== 'audio') {
      console.log('📨 Message:', type)
    }
    
    switch (type) {
      case 'session.ready':
        console.log('✅ Session ready')
        break

      case 'user_speech_started':
        console.log('🎤 User speaking')
        // Clear playback queue for barge-in
        pcmSinkRef.current?.port.postMessage({ type: 'clear' })
        setSpeaking(false)
        break

      case 'user_speech_stopped':
        console.log('🛑 User stopped')
        break

      case 'transcript':
        if (data.role === 'user' && data.text) {
          setTranscript(data.text)
          addMessage({
            id: crypto.randomUUID(),
            role: 'user',
            content: data.text,
            timestamp: new Date()
          })
        } else if (data.role === 'assistant' && data.delta) {
          setAssistantText(prev => prev + data.delta)
        }
        break

      case 'audio':
        if (data.audio) {
          audioChunkCount.current++
          if (audioChunkCount.current % 50 === 1) {
            console.log(`🔊 Audio chunk #${audioChunkCount.current}`)
          }
          playAudio(data.audio)
        }
        break

      case 'response.complete':
        console.log('✅ Response complete')
        audioChunkCount.current = 0
        if (assistantTextRef.current) {
          addMessage({
            id: crypto.randomUUID(),
            role: 'assistant',
            content: assistantTextRef.current,
            timestamp: new Date()
          })
          setAssistantText('')
        }
        // Delay turning off speaking to let audio finish
        setTimeout(() => setSpeaking(false), 500)
        break

      case 'products':
        // Handle product search results from voice assistant
        console.log('🛒 Products received:', data.data?.found || 0)
        if (data.data?.products) {
          // Fetch full product details from API for display
          fetchFullProducts(data.data.products)
        }
        break

      case 'error':
        console.error('❌ Error:', data.message)
        break

      default:
        console.log('Unknown message type:', type)
    }
  }, [addMessage, playAudio, setSpeaking, fetchFullProducts])

  // Start voice session
  const startSession = useCallback(async () => {
    if (isActiveRef.current) return
    
    try {
      console.log('🎯 Starting voice session...')
      
      // Initialize playback first
      await initPlayback()
      
      // Get microphone
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          echoCancellation: true, 
          noiseSuppression: true, 
          autoGainControl: true,
        }
      })
      mediaStreamRef.current = stream
      console.log('🎤 Microphone acquired')
      
      // Create audio context at 24kHz (GPT-4o Realtime expects 24kHz)
      const audioCtx = new AudioContext({ sampleRate: 24000 })
      if (audioCtx.state === 'suspended') await audioCtx.resume()
      audioContextRef.current = audioCtx
      console.log('🎵 Audio context created at', audioCtx.sampleRate, 'Hz')
      
      // Connect WebSocket
      const ws = new WebSocket(`${BACKEND_WS_URL}/api/v1/realtime/ws`)
      wsRef.current = ws
      
      ws.onopen = () => {
        console.log('🔌 WebSocket connected')
        setConnected(true)
        
        // Start audio capture inline here to capture the right refs
        console.log('🎙️ Starting audio capture...')
        
        const source = audioCtx.createMediaStreamSource(stream)
        sourceRef.current = source
        
        const processor = audioCtx.createScriptProcessor(4096, 1, 1)
        processorRef.current = processor
        
        let chunksSent = 0
        
        processor.onaudioprocess = (e) => {
          if (!isActiveRef.current) return
          if (!ws || ws.readyState !== WebSocket.OPEN) return
          
          const float32 = e.inputBuffer.getChannelData(0)
          
          // Check audio level
          let sum = 0
          for (let i = 0; i < float32.length; i++) {
            sum += Math.abs(float32[i])
          }
          const avgLevel = sum / float32.length
          
          // Convert Float32 [-1, 1] to Int16 PCM
          const int16 = new Int16Array(float32.length)
          for (let i = 0; i < float32.length; i++) {
            const s = Math.max(-1, Math.min(1, float32[i]))
            int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
          }
          
          // Convert to base64
          const uint8 = new Uint8Array(int16.buffer)
          let binary = ''
          for (let i = 0; i < uint8.length; i++) {
            binary += String.fromCharCode(uint8[i])
          }
          const base64 = btoa(binary)
          
          // Send to backend
          ws.send(JSON.stringify({
            type: 'input_audio_buffer.append',
            audio: base64
          }))
          
          chunksSent++
          if (chunksSent % 20 === 1) {
            console.log(`📤 Sent ${chunksSent} audio chunks (level: ${avgLevel.toFixed(4)}, size: ${base64.length})`)
          }
        }
        
        // Connect: source -> processor -> destination
        source.connect(processor)
        processor.connect(audioCtx.destination)
        
        console.log('🎙️ Audio capture started!')
      }

      ws.onmessage = (event) => {
        try {
          handleServerMessage(JSON.parse(event.data))
        } catch (e) {
          console.error('Parse error:', e)
        }
      }

      ws.onerror = (err) => {
        console.error('❌ WebSocket error:', err)
        setConnected(false)
      }
      
      ws.onclose = () => {
        console.log('🔌 WebSocket closed')
        setConnected(false)
        stopSession()
      }

      isActiveRef.current = true
      setListening(true)
      
    } catch (error) {
      console.error('❌ Session start failed:', error)
      alert('Please allow microphone access and try again')
    }
  }, [setConnected, setListening, handleServerMessage, initPlayback])

  // Stop session
  const stopSession = useCallback(() => {
    console.log('🛑 Stopping session...')
    isActiveRef.current = false
    
    // Disconnect processor
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }
    if (sourceRef.current) {
      sourceRef.current.disconnect()
      sourceRef.current = null
    }
    
    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {})
      audioContextRef.current = null
    }
    
    // Stop mic
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(t => t.stop())
      mediaStreamRef.current = null
    }
    
    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    setListening(false)
    setConnected(false)
    console.log('✅ Session stopped')
  }, [setListening, setConnected])

  // Toggle session
  const toggleSession = useCallback(async () => {
    if (isActiveRef.current) {
      stopSession()
    } else {
      await startSession()
    }
  }, [startSession, stopSession])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isActiveRef.current = false
      processorRef.current?.disconnect()
      sourceRef.current?.disconnect()
      audioContextRef.current?.close().catch(() => {})
      playbackContextRef.current?.close().catch(() => {})
      mediaStreamRef.current?.getTracks().forEach(t => t.stop())
      wsRef.current?.close()
    }
  }, [])

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
          onClick={toggleSession}
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
