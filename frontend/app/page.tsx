
"use client";

import { useState, useRef, useEffect } from "react";
import { Send, ShoppingBag, Star, Menu, Search, Pizza, Utensils, X, MessageSquare, Loader2 } from "lucide-react";

type Message = {
  role: "user" | "assistant";
  content: string;
  isTool?: boolean;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState(() => "user_" + Math.random().toString(36).substring(7));
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:4000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          message: text,
          session_id: sessionId,
        }),
      });

      if (!response.ok) throw new Error("Network response was not ok");

      const data = await response.json();
      if (data.session_id) setSessionId(data.session_id);

      const assistantMessage: Message = {
        role: "assistant",
        content: data.response_text,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      if (data.tool_calls && data.tool_calls.length > 0) {
        // Optional: Display tool usage if desired
        /*
        data.tool_calls.forEach((tool: any) => {
            if (tool.type === 'function_call') {
                setMessages(prev => [...prev, { role: 'assistant', content: `Using tool: ${tool.name}`, isTool: true }]);
            }
        });
        */
      }

    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I encountered an error connecting to the concierge." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (action: string) => {
    handleSend(action);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans">
      {/* Header */}
      <header className="bg-white sticky top-0 z-50 shadow-sm border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer">
            <Menu className="w-6 h-6 text-gray-700 md:hidden" />
            <div className="text-[#FF3008] font-bold text-2xl tracking-tight flex items-center gap-1">
              Concierge<span className="text-gray-800 font-extrabold">Eats</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button className="bg-gray-100 px-4 py-2 rounded-full text-sm font-semibold text-gray-700 hidden md:flex items-center gap-2 hover:bg-gray-200 transition">
              <ShoppingBag className="w-4 h-4" />
              <span>Orders</span>
            </button>
            <div className="w-10 h-10 bg-[#FF3008] rounded-full flex items-center justify-center text-white font-bold cursor-pointer hover:bg-[#E02906] transition">
              U
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full p-4 md:p-6 flex flex-col gap-6">

        {/* Hero Section */}
        {messages.length === 0 && (
          <div className="bg-[#FF3008] rounded-3xl p-8 md:p-12 text-white relative overflow-hidden shadow-lg animate-fade-in-up">
            <div className="relative z-10 max-w-lg">
              <h1 className="text-4xl md:text-5xl font-extrabold mb-4 leading-tight">
                Craving something delicious?
              </h1>
              <p className="text-lg md:text-xl opacity-90 mb-8 font-medium">
                Your personal AI concierge for the best burgers and pizzas in town.
              </p>
              <div className="relative group">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5 group-focus-within:text-[#FF3008] transition-colors" />
                <input
                  type="text"
                  placeholder="What are you in the mood for?"
                  className="w-full h-14 pl-12 pr-4 rounded-full text-gray-800 font-medium shadow-md focus:outline-none focus:ring-4 focus:ring-white/30 transition-all placeholder:text-gray-400"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSend(e.currentTarget.value);
                    }
                  }}
                />
              </div>
            </div>

            {/* Decorative background elements */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-black/10 rounded-full blur-2xl translate-y-1/2 -translate-x-1/4"></div>
          </div>
        )}

        {/* Vendors Section */}
        {messages.length === 0 && (
          <section className="animate-fade-in-up animation-delay-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-800">Featured Vendors</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Burger Card */}
              <div
                onClick={() => handleQuickAction("I want to see the burger menu")}
                className="group bg-white rounded-2xl p-4 shadow-sm border border-transparent hover:border-[#FF3008]/20 hover:shadow-md transition-all cursor-pointer flex gap-4 items-center"
              >
                <div className="w-24 h-24 bg-orange-100 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                  <Utensils className="w-10 h-10 text-orange-500" />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-900 group-hover:text-[#FF3008] transition-colors">Burger Joint</h3>
                  <div className="flex items-center gap-1 text-sm text-gray-500 mb-1">
                    <span className="bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-bold text-xs">4.8</span>
                    <Star className="w-3 h-3 fill-current text-yellow-400" />
                    <span>• American • $$</span>
                  </div>
                  <p className="text-sm text-gray-400">Classic cheseburgers & spicy options.</p>
                </div>
              </div>

              {/* Pizza Card */}
              <div
                onClick={() => handleQuickAction("I want to see the pizza menu")}
                className="group bg-white rounded-2xl p-4 shadow-sm border border-transparent hover:border-[#FF3008]/20 hover:shadow-md transition-all cursor-pointer flex gap-4 items-center"
              >
                <div className="w-24 h-24 bg-red-100 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                  <Pizza className="w-10 h-10 text-red-500" />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-900 group-hover:text-[#FF3008] transition-colors">Pizza Place</h3>
                  <div className="flex items-center gap-1 text-sm text-gray-500 mb-1">
                    <span className="bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-bold text-xs">4.9</span>
                    <Star className="w-3 h-3 fill-current text-yellow-400" />
                    <span>• Italian • $$$</span>
                  </div>
                  <p className="text-sm text-gray-400">Authentic pepperoni & veggie pizzas.</p>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Chat Interface */}
        <section className={`flex-1 bg-white rounded-3xl shadow-sm border border-gray-100 flex flex-col overflow-hidden transition-all duration-500 ${messages.length === 0 ? 'min-h-[200px]' : 'min-h-[500px]'}`}>
          <div className="p-4 border-b border-gray-50 bg-gray-50/50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              <span className="font-semibold text-sm text-gray-600">Concierge Active</span>
            </div>
            {messages.length > 0 && (
              <button
                onClick={() => setMessages([])}
                className="text-xs font-medium text-gray-400 hover:text-red-500 flex items-center gap-1 transition-colors"
              >
                <X className="w-3 h-3" /> Clear Chat
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 opacity-50">
                <MessageSquare className="w-12 h-12 text-gray-300 mb-2" />
                <p className="text-gray-400 text-sm">Start a conversation to order from multiple stores at once!</p>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-5 py-3.5 text-sm md:text-base leading-relaxed shadow-sm ${msg.role === 'user'
                    ? 'bg-[#FF3008] text-white rounded-br-none'
                    : 'bg-gray-100 text-gray-800 rounded-bl-none prose prose-sm'
                    }`}
                >
                  {msg.role === 'assistant' ? (
                    <div className="markdown-content whitespace-pre-wrap">{msg.content}</div>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start w-full">
                <div className="bg-gray-100 rounded-2xl rounded-bl-none px-5 py-4 flex items-center gap-2">
                  <span className="text-xs text-gray-500 font-medium">Concierge is thinking</span>
                  <Loader2 className="w-4 h-4 text-[#FF3008] animate-spin" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 bg-white border-t border-gray-100">
            <div className="relative flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend(input)}
                placeholder="Type your order or question..."
                disabled={isLoading}
                className="flex-1 bg-gray-100 hover:bg-gray-50 focus:bg-white border border-transparent focus:border-gray-200 rounded-full py-3.5 pl-6 pr-12 focus:outline-none focus:ring-2 focus:ring-[#FF3008]/20 transition-all text-gray-800 placeholder:text-gray-400"
              />
              <button
                onClick={() => handleSend(input)}
                disabled={!input.trim() || isLoading}
                className="absolute right-1.5 p-2 bg-[#FF3008] text-white rounded-full hover:bg-[#E02906] disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow-md transform hover:scale-105 active:scale-95"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </section>

      </main>
    </div>
  );
}
