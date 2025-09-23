// src/components/ChatBox.jsx
import { useEffect, useRef, useState } from "react";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";
import api from "../api/apiClient";

export default function ChatBox({ articleId }) {
  const [messages, setMessages] = useState([
    { sender: "ai", text: "Ask Anything" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage() {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post("/api/v1/ask", {
        question: input,
        context_ids: [articleId], // ✅ correct id now
      });

      const aiMessage = { sender: "ai", text: res.data.answer };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error("Chat API error:", err);
      setMessages((prev) => [
        ...prev,
        { sender: "ai", text: "Sorry, something went wrong." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="w-full max-w-2xl bg-[#343c51] rounded-2xl p-6 shadow-md mt-8 text-gray-200 flex flex-col max-h-screen">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`px-4 py-2 rounded-xl shadow-md text-sm ${msg.sender === "user"
                ? "bg-[#2a3245] ml-auto w-fit max-w-sm"
                : "bg-[#1e2533] mr-auto w-fit max-w-2xl"
              }`}
          >
            {msg.text}
          </div>
        ))}

        {loading && (
          <div className="bg-[#1e2533] w-fit max-w-xs px-4 py-2 rounded-xl shadow-md text-sm mr-auto italic text-gray-400">
            AI is typing…
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="mt-4 flex items-center bg-[#2a3245] rounded-xl px-4 py-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your question..."
          className="flex-1 bg-transparent outline-none text-gray-200 placeholder-gray-400"
        />
        <button
          onClick={sendMessage}
          className="ml-2 text-gray-300 hover:text-white transition"
        >
          <PaperAirplaneIcon className="w-6 h-6" />
        </button>
      </div>
    </div>
  );
}
