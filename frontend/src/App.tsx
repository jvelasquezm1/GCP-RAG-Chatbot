import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import {
  Trash2,
  Loader2,
  Send,
  MessageSquare,
  AlertTriangle,
  Upload,
  CheckCircle2,
} from "lucide-react";
import config from "./config";
import "./App.css";
import { Message } from "./types/chat";
import { UserAvatar, AssistantAvatar } from "./components/Avatars";
import { useAutoScroll } from "./hooks/useAutoScroll";

const apiClient = axios.create({
  baseURL: config.apiUrl,
  headers: {
    "Content-Type": "application/json",
  },
});

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    success: boolean;
    message: string;
    filename?: string;
    chunksCreated?: number;
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const messagesEndRef = useAutoScroll([messages, isLoading]);

  // Initialize welcome message on component mount
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage: Message = {
        id: "welcome-message",
        role: "assistant",
        content:
          "👋 Welcome! I am your dedicated assistant specializing in Juan Velasquez. My knowledge is based on specific documented context (RAG) about his career and achievements. What would you like to know about Juan Velasquez today?",
        timestamp: new Date(),
      };
      setMessages([welcomeMessage]);
    }
  }, []);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputMessage.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setError(null);
    setIsLoading(true);

    try {
      const response = await apiClient.post("/chat", {
        message: userMessage.content,
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.data.answer,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        "Failed to send message (API URL is a placeholder)";
      setError(errorMessage);

      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Error: ${errorMessage}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setError(null);
    setTimeout(() => {
      const welcomeMessage: Message = {
        id: "welcome-message",
        role: "assistant",
        content:
          "👋 Welcome! I am your dedicated assistant specializing in Juan Velasquez. My knowledge is based on specific documented context (RAG) about his career and achievements. What would you like to know about him today?",
        timestamp: new Date(),
      };
      setMessages([welcomeMessage]);
    }, 100);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = [
      "application/pdf",
      "text/markdown",
      "text/plain",
      "text/x-markdown",
    ];
    const allowedExtensions = [".pdf", ".md", ".markdown", ".txt"];
    const fileExt = file.name
      .substring(file.name.lastIndexOf("."))
      .toLowerCase();

    if (
      !allowedTypes.includes(file.type) &&
      !allowedExtensions.includes(fileExt)
    ) {
      setError(
        `Unsupported file type. Supported: PDF, Markdown (.md), or Text (.txt)`
      );
      return;
    }

    // Validate file size (10MB max)
    const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
    if (file.size > MAX_FILE_SIZE) {
      setError(`File size exceeds maximum allowed size of 10MB`);
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadStatus(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(`${config.apiUrl}/ingest`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setUploadStatus({
        success: true,
        message: response.data.message,
        filename: response.data.filename,
        chunksCreated: response.data.chunks_created,
      });

      // Add success message to chat
      const successMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: `✅ Document "${response.data.filename}" successfully ingested! ${response.data.chunks_created} chunks created. You can now ask questions about this document.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, successMessage]);
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        "Failed to upload document";
      setError(errorMessage);

      const errorMsg: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: `❌ Upload failed: ${errorMessage}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const MessageBubble: React.FC<{ message: Message; index: number }> = ({
    message,
    index,
  }) => {
    const isUser = message.role === "user";
    const bubbleClasses = isUser
      ? "bg-blue-600 text-white rounded-br-lg"
      : "bg-gray-800 text-gray-100 rounded-bl-lg border border-gray-700";

    return (
      <div
        key={message.id}
        className={`flex items-start space-x-3 transition-opacity duration-300 ${
          isUser ? "flex-row-reverse space-x-reverse" : ""
        } max-w-full`}
        style={{ opacity: 1, animationDelay: `${index * 30}ms` }}
      >
        <div className="pt-1.5">
          {isUser ? <UserAvatar /> : <AssistantAvatar />}
        </div>

        <div
          className={`flex flex-col max-w-full ${
            isUser ? "items-end" : "items-start"
          }`}
        >
          <div
            className={`px-4 py-3 rounded-2xl whitespace-pre-wrap shadow-lg ${bubbleClasses} transition-all duration-300`}
          >
            <p className="text-sm leading-relaxed">{message.content}</p>
          </div>
          <span
            className={`text-xs text-gray-400 mt-1.5 px-1.5 ${
              isUser ? "mr-1" : "ml-1"
            }`}
          >
            {message.timestamp.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white font-sans flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-gray-950 -z-10"></div>

      <div className="bg-gray-900 border border-gray-800 rounded-3xl shadow-2xl flex flex-col w-full max-w-5xl h-[92vh] max-h-[800px] overflow-hidden">
        <div className="bg-gray-800 text-white px-6 py-4 rounded-t-3xl border-b border-gray-700 shadow-xl flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-blue-600 text-white shadow-md">
              <MessageSquare className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                GCP RAG Chatbot
              </h1>
              <p className="text-xs text-gray-400 font-medium">
                RAG Chatbot with Document Ingestion
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.md,.markdown,.txt"
              onChange={handleFileUpload}
              className="hidden"
              disabled={isUploading}
            />
            <button
              onClick={handleUploadClick}
              disabled={isUploading}
              className="p-2 rounded-xl bg-green-700 text-green-100 hover:bg-green-600 active:scale-95 transition duration-200 ease-in-out flex items-center shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
              title="Upload Document"
              aria-label="Upload Document"
            >
              {isUploading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Upload className="w-5 h-5" />
              )}
            </button>
            <button
              onClick={handleClearChat}
              className="p-2 rounded-xl bg-red-700 text-red-100 hover:bg-red-600 active:scale-95 transition duration-200 ease-in-out flex items-center shadow-md"
              title="Clear Chat History"
              aria-label="Clear Chat History"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5 bg-gray-900 custom-scrollbar">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full space-y-4 text-center">
              <div className="bg-gray-800 p-5 rounded-2xl border border-gray-700">
                <MessageSquare className="w-8 h-8 text-indigo-400" />
              </div>
              <div className="text-center space-y-2">
                <h3 className="text-lg font-semibold text-white">
                  Start a conversation
                </h3>
                <p className="text-sm text-gray-400 max-w-md">
                  Send a message to test the chat endpoint.
                </p>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <MessageBubble key={message.id} message={message} index={index} />
          ))}

          {isLoading && (
            <div className="flex items-start space-x-3 transition-opacity duration-300">
              <AssistantAvatar />
              <div className="bg-gray-800 border border-gray-700 px-4 py-3 rounded-2xl rounded-bl-lg shadow-lg">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                  <span className="text-sm text-gray-300 italic">
                    Thinking...
                  </span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {uploadStatus && uploadStatus.success && (
          <div className="bg-green-900/40 border-t-2 border-green-700 px-6 py-3 flex justify-between items-center backdrop-blur-sm shadow-inner">
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="w-5 h-5 text-green-500" />
              <div className="flex flex-col">
                <span className="text-sm text-green-300 font-medium">
                  {uploadStatus.message}
                </span>
                {uploadStatus.chunksCreated !== undefined && (
                  <span className="text-xs text-green-400">
                    {uploadStatus.chunksCreated} chunks created
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={() => setUploadStatus(null)}
              className="text-green-400 hover:text-white transition-colors text-lg leading-none p-1 rounded-full hover:bg-green-700/50"
              aria-label="Dismiss success message"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        )}

        {error && (
          <div className="bg-red-900/40 border-t-2 border-red-700 px-6 py-3 flex justify-between items-center backdrop-blur-sm shadow-inner">
            <div className="flex items-center space-x-3">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <span className="text-sm text-red-300 font-medium">{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-white transition-colors text-lg leading-none p-1 rounded-full hover:bg-red-700/50"
              aria-label="Dismiss error"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        )}

        <div className="border-t border-gray-700 bg-gray-800 px-6 py-4">
          <div className="flex space-x-3">
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                className="w-full h-full px-4 py-3 pr-14 bg-gray-700 border border-gray-600 rounded-xl resize-none focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 transition-all disabled:bg-gray-900 disabled:cursor-not-allowed disabled:opacity-60 text-sm leading-relaxed placeholder:text-gray-500 text-white"
                value={inputMessage}
                onChange={handleInputChange}
                onKeyDown={handleKeyPress}
                placeholder="Type your message... (Enter to send)"
                rows={1}
                disabled={isLoading}
                maxLength={1000}
              />
              <div className="absolute right-3 bottom-3 text-xs text-gray-500 font-medium">
                {inputMessage.length}/1000
              </div>
            </div>
            <button
              className="px-5 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center space-x-2 min-w-[90px] shadow-lg shadow-blue-500/25"
              onClick={handleSendMessage}
              disabled={isLoading || !inputMessage.trim()}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <span className="text-sm hidden sm:inline">Send</span>
                  <Send className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
