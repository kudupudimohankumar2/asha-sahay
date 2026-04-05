import { useEffect, useState, useRef } from "react";
import {
  Send,
  RotateCcw,
  User,
  Bot,
  ChevronDown,
  AlertCircle,
  BookOpen,
  ShieldAlert,
  FileText,
} from "lucide-react";
import { api } from "../api/client";
import RiskBadge from "../components/RiskBadge";
import LoadingSpinner from "../components/LoadingSpinner";

const LANGUAGES = [
  { code: "hi", label: "Hindi (हिन्दी)" },
  { code: "en", label: "English" },
  { code: "kn", label: "Kannada (ಕನ್ನಡ)" },
  { code: "te", label: "Telugu (తెలుగు)" },
  { code: "ta", label: "Tamil (தமிழ்)" },
  { code: "mr", label: "Marathi (मराठी)" },
  { code: "bn", label: "Bengali (বাংলা)" },
  { code: "gu", label: "Gujarati (ગુજરાતી)" },
  { code: "ml", label: "Malayalam (മലയാളം)" },
  { code: "pa", label: "Punjabi (ਪੰਜਾਬੀ)" },
];

const MODES = [
  { id: "general", label: "General" },
  { id: "risk_check", label: "Risk Check" },
  { id: "ration", label: "Nutrition" },
  { id: "schedule", label: "Schedule" },
];

export default function AIAssistant() {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState("");
  const [lang, setLang] = useState("hi");
  const [mode, setMode] = useState("general");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingPatients, setLoadingPatients] = useState(true);
  const chatEndRef = useRef(null);

  useEffect(() => {
    api.getPatients().then((p) => {
      setPatients(p);
      setLoadingPatients(false);
    });
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !selectedPatient || sending) return;

    const userMsg = { role: "user", text: input.trim() };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setSending(true);

    try {
      const result = await api.chat(selectedPatient, {
        text: userMsg.text,
        source_language: lang,
        mode,
      });

      const aiMsg = {
        role: "assistant",
        text: result.translated_response || result.ai_response || "No response",
        original: result.original_text,
        translated_query: result.translated_query,
        red_flag: result.red_flag,
        guidelines: result.retrieved_guidelines,
        triggered_rules: result.triggered_rules,
        risk_summary: result.risk_summary,
        confidence: result.confidence,
      };
      setMessages((m) => [...m, aiMsg]);
    } catch (err) {
      setMessages((m) => [...m, { role: "error", text: err.message }]);
    } finally {
      setSending(false);
    }
  };

  const selectedPatientData = patients.find((p) => p.patient_id === selectedPatient);

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)] animate-fade-in">
      {/* Config bar */}
      <div className="card mb-4 shrink-0">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="label">Patient</label>
            {loadingPatients ? (
              <div className="input-field text-gray-400">Loading...</div>
            ) : (
              <select
                className="input-field"
                value={selectedPatient}
                onChange={(e) => {
                  setSelectedPatient(e.target.value);
                  setMessages([]);
                }}
              >
                <option value="">Select a patient...</option>
                {patients.map((p) => (
                  <option key={p.patient_id} value={p.patient_id}>
                    {p.full_name} — {p.village} ({p.risk_band})
                  </option>
                ))}
              </select>
            )}
          </div>
          <div>
            <label className="label">Language</label>
            <select className="input-field" value={lang} onChange={(e) => setLang(e.target.value)}>
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Mode</label>
            <select className="input-field" value={mode} onChange={(e) => setMode(e.target.value)}>
              {MODES.map((m) => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </select>
          </div>
        </div>
        {selectedPatientData && (
          <div className="mt-3 flex items-center gap-3 text-sm text-gray-500">
            <RiskBadge risk={selectedPatientData.risk_band} />
            <span>{selectedPatientData.trimester || "—"} trimester</span>
            <span>{selectedPatientData.gestational_weeks ? `${selectedPatientData.gestational_weeks}w` : ""}</span>
          </div>
        )}
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto rounded-xl border border-gray-200 bg-white p-4 space-y-4 mb-4">
        {!selectedPatient && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Bot className="w-12 h-12 text-gray-300 mb-3" />
            <p className="text-gray-500 font-medium">Select a patient to start chatting</p>
            <p className="text-sm text-gray-400 mt-1 max-w-sm">
              Ask health questions in any Indian language. The AI will respond with patient-aware, guideline-grounded answers.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} msg={msg} />
        ))}

        {sending && (
          <div className="flex items-center gap-3 p-4">
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
              <Bot className="w-4 h-4 text-primary-600" />
            </div>
            <div className="flex gap-1">
              <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input bar */}
      <div className="flex gap-2 shrink-0">
        <input
          className="input-field flex-1"
          placeholder={selectedPatient ? "Type your question..." : "Select a patient first"}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          disabled={!selectedPatient || sending}
        />
        <button
          onClick={handleSend}
          disabled={!selectedPatient || !input.trim() || sending}
          className="btn-primary px-5"
        >
          <Send className="w-4 h-4" />
        </button>
        <button
          onClick={() => setMessages([])}
          className="btn-secondary px-3"
          title="Clear chat"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}


function ChatMessage({ msg }) {
  const [showEvidence, setShowEvidence] = useState(false);
  const isUser = msg.role === "user";
  const isError = msg.role === "error";

  if (isError) {
    return (
      <div className="flex justify-center">
        <div className="px-4 py-2 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">
          {msg.text}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : ""} animate-slide-up`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
          <Bot className="w-4 h-4 text-primary-600" />
        </div>
      )}

      <div className={`max-w-[80%] ${isUser ? "order-first" : ""}`}>
        {msg.red_flag && (
          <div className="mb-2 px-3 py-2 rounded-lg bg-red-50 border border-red-200 flex items-center gap-2 text-sm text-red-700">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span className="font-semibold">Emergency flags detected — take immediate action</span>
          </div>
        )}

        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-primary-600 text-white rounded-br-md"
              : "bg-gray-100 text-gray-800 rounded-bl-md"
          }`}
        >
          {msg.text}
        </div>

        {/* Evidence drawer for AI messages */}
        {!isUser && (msg.guidelines?.length > 0 || msg.triggered_rules?.length > 0 || msg.risk_summary) && (
          <div className="mt-2">
            <button
              onClick={() => setShowEvidence(!showEvidence)}
              className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-primary-600 transition-colors"
            >
              <BookOpen className="w-3 h-3" />
              Evidence & Context
              <ChevronDown className={`w-3 h-3 transition-transform ${showEvidence ? "rotate-180" : ""}`} />
            </button>

            {showEvidence && (
              <div className="mt-2 p-3 rounded-lg bg-gray-50 border border-gray-200 space-y-3 text-xs animate-fade-in">
                {msg.guidelines?.length > 0 && (
                  <div>
                    <h5 className="font-semibold text-gray-700 mb-1 flex items-center gap-1">
                      <FileText className="w-3 h-3" /> Retrieved Guidelines
                    </h5>
                    {msg.guidelines.slice(0, 3).map((g, j) => (
                      <div key={j} className="p-2 rounded bg-white border border-gray-100 mb-1">
                        <span className="font-medium">[{g.source}]</span> (relevance: {g.score?.toFixed(2)})
                        <p className="text-gray-600 mt-0.5">{g.text?.slice(0, 200)}...</p>
                      </div>
                    ))}
                  </div>
                )}

                {msg.triggered_rules?.length > 0 && (
                  <div>
                    <h5 className="font-semibold text-gray-700 mb-1 flex items-center gap-1">
                      <ShieldAlert className="w-3 h-3" /> Triggered Rules
                    </h5>
                    {msg.triggered_rules.map((r, j) => (
                      <div key={j} className="p-2 rounded bg-amber-50 border border-amber-100 mb-1">
                        <span className="font-medium">{r.name}</span> ({r.severity}) — {r.details}
                      </div>
                    ))}
                  </div>
                )}

                {msg.risk_summary && (
                  <div>
                    <h5 className="font-semibold text-gray-700 mb-1">Risk Summary</h5>
                    <p className="text-gray-600">{msg.risk_summary}</p>
                  </div>
                )}

                {msg.confidence != null && (
                  <p className="text-gray-400">Confidence: {(msg.confidence * 100).toFixed(0)}%</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0">
          <User className="w-4 h-4 text-gray-600" />
        </div>
      )}
    </div>
  );
}
