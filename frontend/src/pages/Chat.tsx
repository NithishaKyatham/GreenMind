import React, { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "../api/disease";
import { useLanguage } from "../context/LanguageContext";
import { useVoice } from "../hooks/useVoice";

interface Message {
  role: "user" | "assistant";
  content: string;
  mode?: string;
}

const Chat: React.FC = () => {
  const { locale } = useLanguage();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [voiceReplies, setVoiceReplies] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const voice = useVoice(locale);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (overrideText?: string) => {
    const text = overrideText ?? input;
    if (!text.trim()) return;
    const userMessage: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    try {
      const res = await sendChatMessage(userMessage.content, conversationId);
      setConversationId(res.data.conversation_id);
      setMessages((prev) => [...prev, { role: "assistant", content: res.data.reply, mode: res.data.mode }]);
      if (voiceReplies) voice.speak(res.data.reply);
    } catch {
      const errMsg = "Sorry, something went wrong. Please try again.";
      setMessages((prev) => [...prev, { role: "assistant", content: errMsg }]);
    } finally {
      setLoading(false);
    }
  };

  const handleMicClick = () => {
    if (voice.listening) {
      voice.stopListening();
      return;
    }
    voice.startListening((transcript) => {
      setInput(transcript);
      handleSend(transcript);
    });
  };

  return (
    <div className="max-w-2xl mx-auto p-6 flex flex-col h-[calc(100vh-140px)]">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold text-primary-700">GreenMind Assistant</h1>
        {voice.supported && (
          <label className="flex items-center gap-2 text-xs text-gray-500">
            <input type="checkbox" checked={voiceReplies} onChange={(e) => setVoiceReplies(e.target.checked)} />
            Speak replies
          </label>
        )}
      </div>
      <p className="text-xs text-gray-500 mb-4">
        Provides general agricultural guidance and does not replace a qualified expert for severe or uncertain cases.
      </p>

      {voice.error && (
        <div className="bg-yellow-50 text-yellow-800 text-xs p-2 rounded mb-2 border border-yellow-200">
          {voice.error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto bg-white rounded-lg border shadow-sm p-4 space-y-3 mb-4">
        {messages.length === 0 && (
          <p className="text-gray-400 text-sm text-center mt-8">
            Ask about crop diseases, symptoms, fertilizer, pests, or weather-related crop care.
            {voice.supported && " Or tap the microphone to speak your question."}
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
              m.role === "user" ? "bg-primary-600 text-white" : "bg-gray-100 text-gray-800"
            }`}>
              {m.content}
              {m.mode === "rule_based_fallback" && (
                <p className="text-[10px] opacity-70 mt-1">Basic Assistant Mode (no AI API key configured)</p>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask GreenMind Assistant about crop diseases, fertilizer, pests..."
          className="flex-1 border rounded px-3 py-2"
        />
        {voice.supported && (
          <button
            onClick={handleMicClick}
            title={voice.listening ? "Stop listening" : "Speak your question"}
            className={`px-3 py-2 rounded font-medium border ${
              voice.listening ? "bg-red-500 text-white border-red-500 animate-pulse" : "border-gray-300 hover:bg-gray-50"
            }`}
          >
            🎤
          </button>
        )}
        <button onClick={() => handleSend()} disabled={loading}
          className="bg-primary-600 text-white px-4 py-2 rounded font-medium disabled:opacity-50">
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
};

export default Chat;
