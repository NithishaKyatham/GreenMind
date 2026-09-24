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
  const { locale, t } = useLanguage();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [voiceReplies, setVoiceReplies] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const voice = useVoice(locale);

  useEffect(() => {
    // Older embedded browsers and test DOMs may not implement this optional
    // browser convenience API. Chat must remain usable when it is absent.
    if (typeof bottomRef.current?.scrollIntoView === "function") {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleSend = async (overrideText?: string) => {
    const text = overrideText ?? input;
    if (!text.trim()) return;
    const userMessage: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    try {
      const res = await sendChatMessage(userMessage.content, conversationId, locale);
      setConversationId(res.data.conversation_id);
      setMessages((prev) => [...prev, { role: "assistant", content: res.data.reply, mode: res.data.mode }]);
      if (voiceReplies) voice.speak(res.data.reply);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: t("chat_error") }]);
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

  const quickActions = [
    { label: t("chat_quick_explain_diagnosis"), message: "Can you explain my most recent diagnosis?" },
    { label: t("chat_quick_what_now"), message: "What should I do now based on my last diagnosis?" },
    { label: t("chat_quick_organic"), message: "What organic treatment options are there for my last diagnosis?" },
    { label: t("chat_quick_prevention"), message: "How can I prevent this disease in the future?" },
    { label: t("chat_quick_weather"), message: "What's the weather like right now?" },
    { label: t("chat_quick_report"), message: "Can you generate a report for my last diagnosis?" },
  ];

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6 flex flex-col h-[calc(100vh-248px)] md:h-[calc(100vh-112px)]">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-semibold text-earth-900">{t("chat_title")}</h1>
        {voice.supported && (
          <label className="flex items-center gap-2 text-xs text-earth-500">
            <input type="checkbox" checked={voiceReplies} onChange={(e) => setVoiceReplies(e.target.checked)} />
            {t("chat_speak_replies")}
          </label>
        )}
      </div>
      <p className="text-xs text-earth-500 mb-4">
        {t("chat_disclaimer")}
      </p>

      {voice.error && (
        <div className="bg-accent-50 text-accent-700 text-xs p-2 rounded-md mb-2 border border-accent-100">
          {voice.error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto bg-white rounded-lg border border-earth-200 shadow-soft p-4 space-y-3 mb-4">
        {messages.length === 0 && (
          <div className="mt-4">
            <p className="text-earth-400 text-sm text-center mb-5">
              {t("chat_empty_prompt")}
              {voice.supported && ` ${t("chat_empty_prompt_voice")}`}
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => handleSend(action.message)}
                  className="text-xs font-medium border border-earth-200 rounded-full px-3 py-1.5 text-earth-700 hover:bg-earth-50 hover:border-primary-300 transition-colors"
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
              m.role === "user" ? "bg-primary-600 text-white" : "bg-earth-100 text-earth-800"
            }`}>
              {m.content}
              {m.mode === "rule_based_fallback" && (
                <p className="text-[10px] opacity-70 mt-1">{t("chat_basic_mode_notice")}</p>
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
          placeholder={t("chat_placeholder")}
          className="flex-1 border border-earth-200 rounded-md px-3 py-2 bg-white"
        />
        {voice.supported && (
          <button
            onClick={handleMicClick}
            title={voice.listening ? t("chat_mic_stop") : t("chat_mic_start")}
            className={`px-3 py-2 rounded-md font-medium border ${
              voice.listening ? "bg-danger-500 text-white border-danger-500 animate-pulse" : "border-earth-200 hover:bg-earth-50"
            }`}
          >
            🎤
          </button>
        )}
        <button onClick={() => handleSend()} disabled={loading}
          className="bg-primary-600 text-white px-4 py-2 rounded-md font-medium hover:bg-primary-700 disabled:opacity-50">
          {loading ? "..." : t("chat_send")}
        </button>
      </div>
    </div>
  );
};

export default Chat;
