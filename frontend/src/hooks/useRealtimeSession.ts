/**
 * Shared Realtime Session Hook
 * Manages WebSocket connection and audio for voice/chat communication
 * Can be used by both VoiceAssistant and ChatPanel
 */
import { useRef, useCallback, useState, useEffect } from 'react'
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
`

export interface UseRealtimeSessionReturn {
  // State
  isConnected: boolean
  isListening: boolean
  isSpeaking: boolean
  transcript: string
  assistantText: string
  
  // Actions
  startVoiceSession: () => Promise<void>
  stopVoiceSession: () => void
  toggleVoiceSession: () => Promise<void>
  sendTextMessage: (text: string) => Promise<void>
  isSessionActive: () => boolean
}

export function useRealtimeSession(): UseRealtimeSessionReturn {
  const {
    isListening,
    isSpeaking,
    isConnected,
    setListening,
    setSpeaking,
    setConnected,
    addMessage,
    setProducts,
    addToCart,
    removeFromCart,
    clearCart,
    setCartOpen,
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
  const sessionReadyRef = useRef(false)
  const sessionReadyResolveRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    assistantTextRef.current = assistantText
  }, [assistantText])

  // Search counter to track which search is current
  const searchCounterRef = useRef(0)

  // Fetch full product details from the API based on voice search results
  const fetchFullProducts = useCallback(async (partialProducts: Array<{ id: string; name: string }>) => {
    try {
      if (!partialProducts || partialProducts.length === 0) {
        console.log('⚠️ No products to fetch')
        return
      }

      searchCounterRef.current += 1
      const thisSearchId = searchCounterRef.current

      console.log(`🔍 [Search #${thisSearchId}] Starting search:`, partialProducts.map(p => p.name))

      // Clear previous products IMMEDIATELY
      setProducts([], true)

      // Search for each product by name to get full details
      const searchPromises = partialProducts.slice(0, 5).map(async (p) => {
        const searchResponse = await fetch(
          `${BACKEND_URL}/api/v1/products/search?query=${encodeURIComponent(p.name)}&limit=1`
        )
        if (searchResponse.ok) {
          const data = await searchResponse.json()
          return data.products?.[0] || null
        }
        return null
      })

      const results = await Promise.all(searchPromises)

      // Check if this is still the latest search
      if (thisSearchId !== searchCounterRef.current) {
        console.log(`⏭️ [Search #${thisSearchId}] Discarding stale results`)
        return
      }

      const validProducts = results.filter(p => p !== null)

      // Deduplicate products by ID
      const uniqueProducts = validProducts.filter((product, index, self) =>
        index === self.findIndex(p => p.id === product.id)
      )

      if (uniqueProducts.length > 0 && thisSearchId === searchCounterRef.current) {
        setProducts(uniqueProducts, true)
        console.log(`✅ [Search #${thisSearchId}] Updated products:`, uniqueProducts.length)
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

  // Play audio via AudioWorklet
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
        sessionReadyRef.current = true
        // Resolve any pending session ready promise
        if (sessionReadyResolveRef.current) {
          sessionReadyResolveRef.current()
          sessionReadyResolveRef.current = null
        }
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
        setTimeout(() => setSpeaking(false), 500)
        break

      case 'products':
        console.log('🛒 Products received:', data.data?.found || 0)
        if (data.data?.products) {
          fetchFullProducts(data.data.products)
        }
        break

      case 'cart_action':
        console.log('🛒 Cart action:', data.action, data.data)
        if (data.action === 'add_to_cart' && data.data?.product) {
          const product = data.data.product
          addToCart({
            id: product.id,
            name: product.name,
            description: product.description || '',
            category: product.category || '',
            subcategory: product.subcategory || '',
            brand: product.brand || '',
            sku: product.sku || '',
            price: product.price,
            sale_price: product.sale_price,
            rating: product.rating || 0,
            review_count: product.review_count || 0,
            in_stock: product.in_stock !== false,
            image_url: product.image_url || '',
            featured: product.featured
          }, data.data.quantity || 1)
        } else if (data.action === 'view_cart') {
          setCartOpen(true)
        } else if (data.action === 'remove_from_cart' && data.data?.product_id) {
          removeFromCart(data.data.product_id)
        } else if (data.action === 'clear_cart') {
          clearCart()
        }
        break

      case 'error':
        console.error('❌ Error:', data.message)
        break

      default:
        console.log('Unknown message type:', type)
    }
  }, [addMessage, playAudio, setSpeaking, fetchFullProducts, addToCart, removeFromCart, clearCart, setCartOpen])

  // Connect WebSocket (without audio capture - for text-only mode)
  const connectWebSocket = useCallback(async (): Promise<WebSocket> => {
    // Initialize playback first
    await initPlayback()
    
    // Reset session ready state
    sessionReadyRef.current = false

    return new Promise((resolve, reject) => {
      const ws = new WebSocket(`${BACKEND_WS_URL}/api/v1/realtime/ws`)

      ws.onopen = () => {
        console.log('🔌 WebSocket connected')
        setConnected(true)
        resolve(ws)
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
        reject(err)
      }

      ws.onclose = () => {
        console.log('🔌 WebSocket closed')
        setConnected(false)
        sessionReadyRef.current = false
        wsRef.current = null
      }

      wsRef.current = ws
    })
  }, [setConnected, handleServerMessage, initPlayback])

  // Send text message via WebSocket
  const sendTextMessage = useCallback(async (text: string) => {
    if (!text.trim()) return

    // Add user message to chat immediately
    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date()
    })

    // Ensure WebSocket is connected
    let ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.log('📡 Connecting WebSocket for text chat...')
      try {
        ws = await connectWebSocket()
      } catch (error) {
        console.error('Failed to connect WebSocket:', error)
        addMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: 'Sorry, I could not connect to the assistant. Please try again.',
          timestamp: new Date()
        })
        return
      }
    }

    // Wait for session to be ready (with timeout)
    if (!sessionReadyRef.current) {
      console.log('⏳ Waiting for session ready...')
      try {
        await Promise.race([
          new Promise<void>(resolve => {
            if (sessionReadyRef.current) {
              resolve()
            } else {
              sessionReadyResolveRef.current = resolve
            }
          }),
          new Promise<void>((_, reject) => 
            setTimeout(() => reject(new Error('Session ready timeout')), 5000)
          )
        ])
      } catch (error) {
        console.error('Session not ready:', error)
        addMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: 'Sorry, the session took too long to initialize. Please try again.',
          timestamp: new Date()
        })
        return
      }
    }

    // Send text message via WebSocket
    console.log('💬 Sending text message:', text)
    ws.send(JSON.stringify({
      type: 'text',
      text: text
    }))
  }, [addMessage, connectWebSocket])

  // Start voice session (with audio capture)
  const startVoiceSession = useCallback(async () => {
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

      // Create audio context at 24kHz
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

        // Start audio capture
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
            const sum = float32.reduce((a, b) => a + Math.abs(b), 0)
            const avgLevel = sum / float32.length
            console.log(`📤 Sent ${chunksSent} audio chunks (level: ${avgLevel.toFixed(4)})`)
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
        stopVoiceSession()
      }

      isActiveRef.current = true
      setListening(true)

    } catch (error) {
      console.error('❌ Session start failed:', error)
      alert('Please allow microphone access and try again')
    }
  }, [setConnected, setListening, handleServerMessage, initPlayback])

  // Stop voice session
  const stopVoiceSession = useCallback(() => {
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

  // Toggle voice session
  const toggleVoiceSession = useCallback(async () => {
    if (isActiveRef.current) {
      stopVoiceSession()
    } else {
      await startVoiceSession()
    }
  }, [startVoiceSession, stopVoiceSession])

  // Check if session is active
  const isSessionActive = useCallback(() => {
    return isActiveRef.current
  }, [])

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

  return {
    isConnected,
    isListening,
    isSpeaking,
    transcript,
    assistantText,
    startVoiceSession,
    stopVoiceSession,
    toggleVoiceSession,
    sendTextMessage,
    isSessionActive,
  }
}
