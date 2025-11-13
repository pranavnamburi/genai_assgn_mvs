import { useState, useRef, useEffect } from "react"
import { MessageCircle, X, Send, Loader2, Image as ImageIcon, Mic, MicOff, Volume2 } from "lucide-react"
import axios from "axios"

const API_BASE_URL = "http://localhost:8000"

export default function MoviChat({ currentPage = "unknown" }) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm Movi, your transport assistant. How can I help you today?",
      sender: "bot",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ])
  const [inputMessage, setInputMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [selectedImage, setSelectedImage] = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [ttsEnabled, setTtsEnabled] = useState(true)
  const fileInputRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const currentAudioRef = useRef(null)

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause()
        currentAudioRef.current = null
      }
    }
  }, [])

  const handleImageSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedImage(file)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        
        // Send audio to backend for STT (Deepgram)
        const formData = new FormData()
        formData.append('audio', audioBlob)
        
        try {
          const response = await axios.post(`${API_BASE_URL}/api/speech-to-text`, formData)
          if (response.data.transcript) {
            setInputMessage(response.data.transcript)
          }
        } catch (error) {
          console.error('Error transcribing audio:', error)
        }

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      console.error('Error accessing microphone:', error)
      alert('Could not access microphone. Please check permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const playTTS = async (text) => {
    if (!ttsEnabled) return

    try {
      setIsSpeaking(true)
      
      // Request TTS audio from backend (ElevenLabs)
      const response = await axios.post(
        `${API_BASE_URL}/api/text-to-speech`,
        { text },
        { responseType: 'blob' }
      )

      // Create audio URL and play
      const audioUrl = URL.createObjectURL(response.data)
      const audio = new Audio(audioUrl)
      currentAudioRef.current = audio

      audio.onended = () => {
        setIsSpeaking(false)
        URL.revokeObjectURL(audioUrl)
        currentAudioRef.current = null
      }

      audio.onerror = () => {
        setIsSpeaking(false)
        console.error('Error playing audio')
      }

      await audio.play()
    } catch (error) {
      console.error('Error with TTS:', error)
      setIsSpeaking(false)
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() && !selectedImage) return

    const userMessageText = inputMessage.trim() || "[Image uploaded]"

    // Add user message to chat
    const newMessage = {
      id: messages.length + 1,
      text: userMessageText,
      sender: "user",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      hasImage: !!selectedImage
    }

    setMessages(prev => [...prev, newMessage])
    setInputMessage("")
    setIsLoading(true)

    try {
      // Prepare form data
      const formData = new FormData()
      formData.append("message", userMessageText)
      formData.append("currentPage", currentPage)
      
      if (selectedImage) {
        formData.append("image", selectedImage)
      }

      // Call backend API
      const response = await axios.post(`${API_BASE_URL}/api/chat`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      // Add bot response to chat
      const botResponse = {
        id: messages.length + 2,
        text: response.data.response,
        sender: "bot",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
      setMessages(prev => [...prev, botResponse])
      
      // Play TTS for bot response
      if (ttsEnabled) {
        playTTS(response.data.response)
      }
      
      // Clear selected image
      setSelectedImage(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }

    } catch (error) {
      console.error("Error communicating with Movi:", error)
      
      // Add error message
      const errorMessage = {
        id: messages.length + 2,
        text: "I apologize, but I'm having trouble connecting to my services. Please make sure the backend server is running.",
        sender: "bot",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      {/* Chat Toggle Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 bg-blue-600 text-white rounded-full p-4 shadow-lg hover:bg-blue-700 transition-all duration-200 z-50 flex items-center gap-2"
          aria-label="Open chat"
        >
          <MessageCircle className="w-6 h-6" />
          <span className="font-medium">Chat with Movi</span>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-white rounded-lg shadow-2xl flex flex-col z-50 border border-gray-200">
          {/* Chat Header */}
          <div className="bg-blue-600 text-white p-4 rounded-t-lg flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-white/20 rounded-full p-2">
                <MessageCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold">Movi Assistant</h3>
                <p className="text-xs text-blue-100">
                  {isSpeaking ? "Speaking..." : isRecording ? "Listening..." : "Online"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setTtsEnabled(!ttsEnabled)}
                className="hover:bg-white/20 rounded-full p-1 transition"
                title={ttsEnabled ? "Disable voice" : "Enable voice"}
              >
                <Volume2 className={`w-5 h-5 ${!ttsEnabled ? 'opacity-50' : ''}`} />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="hover:bg-white/20 rounded-full p-1 transition"
                aria-label="Close chat"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.sender === "user"
                      ? "bg-blue-600 text-white"
                      : message.isError
                      ? "bg-red-50 border border-red-200 text-red-800"
                      : "bg-white border border-gray-200 text-gray-800"
                  }`}
                >
                  <p className="text-sm">{message.text}</p>
                  {message.hasImage && (
                    <span className="text-xs flex items-center gap-1 mt-1">
                      <ImageIcon className="w-3 h-3" />
                      Image attached
                    </span>
                  )}
                  <p
                    className={`text-xs mt-1 ${
                      message.sender === "user" 
                        ? "text-blue-100" 
                        : message.isError
                        ? "text-red-500"
                        : "text-gray-500"
                    }`}
                  >
                    {message.timestamp}
                  </p>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-lg p-3 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  <span className="text-sm text-gray-600">Movi is thinking...</span>
                </div>
              </div>
            )}
          </div>

          {/* Chat Input */}
          <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-200 bg-white rounded-b-lg">
            {selectedImage && (
              <div className="mb-2 flex items-center gap-2 text-xs text-gray-600 bg-blue-50 p-2 rounded">
                <ImageIcon className="w-4 h-4" />
                <span>{selectedImage.name}</span>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedImage(null)
                    if (fileInputRef.current) fileInputRef.current.value = ""
                  }}
                  className="ml-auto text-red-600 hover:text-red-800"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
            <div className="flex gap-2">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageSelect}
                accept="image/*"
                className="hidden"
                id="image-upload"
              />
              <label
                htmlFor="image-upload"
                className="cursor-pointer bg-gray-100 text-gray-600 rounded-full p-2 hover:bg-gray-200 transition"
                title="Upload image"
              >
                <ImageIcon className="w-5 h-5" />
              </label>
              <button
                type="button"
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isLoading}
                className={`rounded-full p-2 transition ${
                  isRecording 
                    ? 'bg-red-500 text-white hover:bg-red-600 animate-pulse' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                title={isRecording ? "Stop recording" : "Start recording"}
              >
                {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={isRecording ? "Recording..." : "Type or speak..."}
                disabled={isLoading || isRecording}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <button
                type="submit"
                disabled={(!inputMessage.trim() && !selectedImage) || isLoading || isRecording}
                className="bg-blue-600 text-white rounded-full p-2 hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Send message"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  )
}

