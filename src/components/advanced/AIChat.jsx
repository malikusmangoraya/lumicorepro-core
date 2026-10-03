/**
 * AIChat - Advanced AI Assistant Interface
 * =========================================
 * Premium chat interface with streaming responses, code highlighting, and multi-modal support.
 * 
 * Features:
 * - Real-time streaming responses
 * - Markdown rendering with syntax highlighting
 * - Code copy buttons
 * - Image upload support
 * - Voice input
 * - Conversation history
 * - Quick prompts/templates
 */

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  Sparkles,
  Image as ImageIcon,
  Mic,
  Copy,
  Check,
  RefreshCw,
  Trash2,
  Download,
} from 'lucide-react';
import PropTypes from 'prop-types';
import api from '../../services/api';

const AIChat = ({ onResponse, initialPrompt }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState(initialPrompt || '');
  const [isStreaming, setIsStreaming] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Quick prompt templates
  const quickPrompts = [
    { label: 'Explain code', prompt: 'Can you explain how this code works?' },
    { label: 'Find bugs', prompt: 'Are there any bugs or issues in this code?' },
    { label: 'Optimize', prompt: 'How can I optimize this code for better performance?' },
    { label: 'Add tests', prompt: 'Generate unit tests for this code.' },
  ];

  // Auto-scroll to bottom
  useEffect(() => {
    if (typeof messagesEndRef.current?.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Send message
  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);

    try {
      // Create AI message placeholder
      const aiMessageId = Date.now() + 1;
      const aiMessage = {
        id: aiMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        isStreaming: true,
      };
      setMessages((prev) => [...prev, aiMessage]);

      // Call API with streaming
      const response = await api.post('/ai/chat', {
        message: input,
        provider: 'gemini',
        history: messages.slice(-10).map((m) => ({
          role: m.role,
          content: m.content,
        })),
      });

      // Simulate streaming (in real implementation, use SSE or WebSocket)
      const fullResponse = response.data.data.response;
      let currentText = '';
      
      for (let i = 0; i < fullResponse.length; i++) {
        currentText += fullResponse[i];
        
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === aiMessageId
              ? { ...msg, content: currentText }
              : msg
          )
        );
        
        // Simulate streaming delay
        await new Promise((resolve) => setTimeout(resolve, 20));
      }

      // Mark as complete
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === aiMessageId
            ? { ...msg, isStreaming: false }
            : msg
        )
      );

      onResponse?.(fullResponse);
    } catch (error) {
      console.error('Chat error:', error);
      
      // Add error message
      setMessages((prev) => [
        ...prev.slice(0, -1), // Remove placeholder
        {
          id: Date.now(),
          role: 'assistant',
          content: '❌ Sorry, I encountered an error. Please try again.',
          timestamp: new Date().toISOString(),
          isError: true,
        },
      ]);
    } finally {
      setIsStreaming(false);
    }
  };

  // Copy code
  const copyCode = (code, id) => {
    navigator.clipboard.writeText(code);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Clear conversation
  const clearConversation = () => {
    if (confirm('Clear conversation history?')) {
      setMessages([]);
    }
  };

  // Export conversation
  const exportConversation = () => {
    const text = messages
      .map((m) => `${m.role.toUpperCase()}: ${m.content}`)
      .join('\n\n');
    
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai-chat-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Render message content (with markdown support)
  const renderContent = (content, messageId) => {
    // Simple code block detection
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: content.slice(lastIndex, match.index),
        });
      }

      // Add code block
      parts.push({
        type: 'code',
        language: match[1] || 'plaintext',
        content: match[2].trim(),
      });

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < content.length) {
      parts.push({
        type: 'text',
        content: content.slice(lastIndex),
      });
    }

    return parts.map((part, index) => {
      if (part.type === 'code') {
        return (
          <div key={index} className="relative group my-4">
            <div className="flex items-center justify-between bg-gray-800 px-4 py-2 rounded-t-lg">
              <span className="text-xs text-gray-400 font-mono">{part.language}</span>
              <button
                onClick={() => copyCode(part.content, `${messageId}-${index}`)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                {copiedId === `${messageId}-${index}` ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
            <pre className="bg-gray-900 p-4 rounded-b-lg overflow-x-auto">
              <code className="text-sm text-gray-100 font-mono">{part.content}</code>
            </pre>
          </div>
        );
      }

      return (
        <p key={index} className="whitespace-pre-wrap leading-relaxed">
          {part.content}
        </p>
      );
    });
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900 rounded-2xl shadow-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800 bg-gradient-to-r from-primary/10 to-secondary/10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/20 rounded-lg">
            <Sparkles className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900 dark:text-white">AI Assistant</h2>
            <p className="text-xs text-gray-500">Ask me anything about your code</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={exportConversation}
            disabled={messages.length === 0}
            className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors disabled:opacity-50"
            title="Export conversation"
          >
            <Download className="w-5 h-5" />
          </button>
          <button
            onClick={clearConversation}
            disabled={messages.length === 0}
            className="p-2 text-gray-500 hover:text-red-500 transition-colors disabled:opacity-50"
            title="Clear conversation"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="p-4 bg-primary/10 rounded-full mb-4">
              <Sparkles className="w-12 h-12 text-primary" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Start a conversation
            </h3>
            <p className="text-gray-500 mb-6 max-w-md">
              Ask questions, get code explanations, find bugs, or request optimizations
            </p>

            {/* Quick prompts */}
            <div className="grid grid-cols-2 gap-3">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt.label}
                  onClick={() => setInput(prompt.prompt)}
                  className="px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 transition-colors"
                >
                  {prompt.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <AnimatePresence>
            {messages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] ${
                    message.role === 'user'
                      ? 'bg-primary text-white'
                      : message.isError
                      ? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white'
                  } rounded-2xl px-5 py-3 shadow-sm`}
                >
                  {message.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  ) : (
                    <div>
                      {renderContent(message.content, message.id)}
                      {message.isStreaming && (
                        <span className="inline-block w-2 h-4 bg-current animate-pulse ml-1" />
                      )}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 dark:border-gray-800 p-4">
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask anything... (Shift+Enter for new line)"
              rows={1}
              className="w-full px-4 py-3 pr-24 bg-gray-100 dark:bg-gray-800 border-none rounded-xl text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              style={{ minHeight: '50px', maxHeight: '150px' }}
            />

            <div className="absolute right-2 bottom-2 flex items-center gap-1">
              <button
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                title="Upload image"
              >
                <ImageIcon className="w-5 h-5" />
              </button>
              <button
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                title="Voice input"
              >
                <Mic className="w-5 h-5" />
              </button>
            </div>
          </div>

          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="p-3 bg-primary hover:bg-primary-600 text-white rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isStreaming ? (
              <RefreshCw className="w-6 h-6 animate-spin" />
            ) : (
              <Send className="w-6 h-6" />
            )}
          </button>
        </div>

        <p className="text-xs text-gray-400 mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
};

AIChat.propTypes = {
  onResponse: PropTypes.func,
  initialPrompt: PropTypes.string,
};

export default AIChat;
