'use client'

import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageCircle, X, Minimize2, Send } from 'lucide-react'
import { v4 as uuidv4 } from 'uuid';

export default function ChatbotWidget({ websiteId }) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef(null)
  const [socket, setSocket] = useState(null)
  const [threadId, setThreadId] = useState(null)

  const toggleChat = () => setIsOpen(!isOpen)

  useEffect(() => {
    // Initialize threadId from localStorage or generate a new one
    const storedThreadId = localStorage.getItem('threadId')
    if (storedThreadId) {
      setThreadId(storedThreadId)
    } else {
      const newThreadId = generateThreadId()
      setThreadId(newThreadId)
      localStorage.setItem('threadId', newThreadId)
    }
  }, [])

  useEffect(() => {
    if (isOpen && threadId) {
      connectWebSocket()
    }

    return () => {
      if (socket) {
        socket.close()
      }
    }
  }, [isOpen, threadId])

  const connectWebSocket = () => {
    const newSocket = new WebSocket(`ws://127.0.0.1:8000/ws/${websiteId}/${threadId}`)

    newSocket.onopen = () => {
      console.log("WebSocket connection established")
    }

    newSocket.onmessage = (event) => {
      console.log("Message from server: ", event.data)
      const data = JSON.parse(event.data)
      if (data.type === 'bot_response') {
        setMessages(prev => [...prev, { id: prev.length + 1, text: data.content, sender: 'bot' }])
        setIsTyping(false)
      } else if (data.type === 'tool_call') {
        // Handle tool call
        const userApproval = confirm(`Approve this action?\n${data.content}`)
        newSocket.send(JSON.stringify({
          approval: userApproval ? 'yes' : 'no'
        }))
      } else if (data.type === 'error') {
        console.error("Error from server:", data.content)
        setMessages(prev => [...prev, { id: prev.length + 1, text: `Error: ${data.content}`, sender: 'bot' }])
      }
    }

    newSocket.onclose = (event) => {
      console.log('WebSocket disconnected', event.code, event.reason)
      if (event.code === 4001) {
        console.error("Invalid website ID")
      } else if (event.code === 4002) {
        console.error("Unauthorized origin")
      } else if (event.code !== 1000) {
        setTimeout(() => {
          console.log('Attempting to reconnect...')
          connectWebSocket()
        }, 3000)
      }
    }

    newSocket.onerror = (error) => {
      console.error("WebSocket Error: ", error)
    }

    setSocket(newSocket)
  }

  const generateThreadId = () => {
    return uuidv4();
  }

  const handleSendMessage = (e) => {
    e.preventDefault()
    if (inputMessage.trim() === '' || !socket) return

    const newMessage = { id: messages.length + 1, text: inputMessage, sender: 'user' }
    setMessages([...messages, newMessage])
    setInputMessage('')
    setIsTyping(true)

    socket.send(JSON.stringify({
      content: inputMessage
    }))
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])


  return (
    <div className="fixed bottom-4 right-4 z-50">
      <AnimatePresence>
        {isOpen ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="bg-white rounded-lg shadow-xl w-80 sm:w-96 h-[70vh] max-h-[600px] flex flex-col"
          >
            <div className="bg-blue-600 text-white p-4 rounded-t-lg flex justify-between items-center">
              <h2 className="text-lg font-semibold">Realtor Chat</h2>
              <div className="flex space-x-2">
                <button onClick={toggleChat} className="p-1 hover:bg-blue-700 rounded">
                  <Minimize2 size={20} />
                </button>
                <button onClick={toggleChat} className="p-1 hover:bg-blue-700 rounded">
                  <X size={20} />
                </button>
              </div>
            </div>
            <div className="flex-grow overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] p-3 rounded-lg break-words whitespace-pre-wrap ${message.sender === 'user' ? 'bg-blue-100 text-blue-900' : 'bg-gray-100'}`}>
                    {message.text}
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 p-3 rounded-lg">
                    <span className="animate-pulse">...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            <form onSubmit={handleSendMessage} className="p-4 border-t">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-grow p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button type="submit" className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 transition-colors">
                  <Send size={20} />
                </button>
              </div>
            </form>
          </motion.div>
        ) : (
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={toggleChat}
            className="bg-blue-600 text-white p-4 rounded-full shadow-lg hover:bg-blue-700 transition-colors"
          >
            <MessageCircle size={24} />
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  )
}
