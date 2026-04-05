const RISK_CONFIG = {
  NORMAL: { bg: "bg-emerald-100", text: "text-emerald-700", dot: "bg-emerald-500", label: "Normal" },
  ELEVATED: { bg: "bg-amber-100", text: "text-amber-700", dot: "bg-amber-500", label: "Elevated" },
  HIGH_RISK: { bg: "bg-orange-100", text: "text-orange-700", dot: "bg-orange-500", label: "High Risk" },
  EMERGENCY: { bg: "bg-red-100", text: "text-red-700", dot: "bg-red-500", label: "Emergency" },
};

export default function RiskBadge({ risk, size = "sm" }) {
  const cfg = RISK_CONFIG[risk] || RISK_CONFIG.NORMAL;
  const sizeClasses = size === "lg" ? "px-3 py-1.5 text-sm" : "px-2 py-0.5 text-xs";

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-medium ${cfg.bg} ${cfg.text} ${sizeClasses}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
}

export function riskColor(risk) {
  return RISK_CONFIG[risk]?.dot?.replace("bg-", "") || "gray-500";
}
