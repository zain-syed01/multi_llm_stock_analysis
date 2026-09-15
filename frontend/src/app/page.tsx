"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Search, ShieldCheck, AlertCircle, Database, Sparkles, Clock } from "lucide-react";

interface ResearchResponse {
  source: string;
  ticker: string;
  current_price?: number;
  trailing_pe?: number;
  created_at: string;
  passed_guardrail: boolean;
  audit_notes?: string;
  final_report: string;
}

export default function Home() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ResearchResponse | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const symbol = ticker.trim().toUpperCase();
    if (!symbol) return;

    setLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/research/${symbol}`, {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error (${response.status})`);
      }

      const result: ResearchResponse = await response.json();
      setData(result);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Unable to connect to backend engine. Ensure FastAPI/Docker is running on port 8000.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 antialiased p-6 md:p-12 font-sans selection:bg-zinc-800">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="border-b border-zinc-800 pb-5">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold tracking-tight text-zinc-100">
                Equity Research Terminal
              </h1>
              <p className="text-xs text-zinc-400 mt-0.5">
                Multi-agent LangGraph engine • ChromaDB vector store • Neon PostgreSQL cache
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-mono text-zinc-400">
                {process.env.NEXT_PUBLIC_API_URL ? "API: LIVE" : "API: 8000"}
              </span>
            </div>
          </div>
        </header>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-zinc-500" />
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="Search ticker (e.g., NVDA, MSFT, AAPL)..."
              className="w-full bg-zinc-900 border border-zinc-800 rounded-md pl-10 pr-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 font-mono uppercase"
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="bg-zinc-100 hover:bg-white text-zinc-950 font-medium px-5 py-2.5 rounded-md text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <span className="h-3.5 w-3.5 border-2 border-zinc-950 border-t-transparent rounded-full animate-spin" />
                <span>Running agents...</span>
              </>
            ) : (
              "Analyze"
            )}
          </button>
        </form>

        {/* Error State */}
        {error && (
          <div className="p-3.5 rounded-md border border-red-900/40 bg-red-950/20 text-red-400 text-xs flex items-center gap-2.5">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Content Section */}
        {data && (
          <div className="space-y-6">
            
            {/* Stat Badges */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3.5 rounded-md border border-zinc-800/80 bg-zinc-900/50">
                <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400">Ticker</span>
                <p className="text-lg font-mono font-semibold text-zinc-100 mt-1">{data.ticker}</p>
              </div>

              <div className="p-3.5 rounded-md border border-zinc-800/80 bg-zinc-900/50">
                <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400">Market Price</span>
                <p className="text-lg font-mono font-semibold text-zinc-100 mt-1">
                  {data.current_price ? `$${data.current_price.toFixed(2)}` : "—"}
                </p>
              </div>

              <div className="p-3.5 rounded-md border border-zinc-800/80 bg-zinc-900/50">
                <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400">Trailing P/E</span>
                <p className="text-lg font-mono font-semibold text-zinc-100 mt-1">
                  {data.trailing_pe ? data.trailing_pe.toFixed(2) : "—"}
                </p>
              </div>

              <div className="p-3.5 rounded-md border border-zinc-800/80 bg-zinc-900/50">
                <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400">Storage State</span>
                <div className="flex items-center gap-1.5 mt-1.5">
                  {data.source === "cache" ? (
                    <span className="inline-flex items-center gap-1 text-xs font-mono text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-900/30">
                      <Database className="h-3 w-3" /> Neon Cache
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-900/30">
                      <Sparkles className="h-3 w-3" /> Live Run
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Audit Status Bar */}
            <div className="p-3 rounded-md border border-zinc-800/80 bg-zinc-900/40 flex items-start justify-between gap-3 text-xs">
              <div className="flex items-center gap-2">
                <ShieldCheck className={`h-4 w-4 ${data.passed_guardrail ? "text-emerald-400" : "text-amber-400"}`} />
                <span className="text-zinc-300">
                  Guardrail Audit: <strong className="font-semibold text-zinc-100">{data.passed_guardrail ? "Passed verification" : "Flagged"}</strong>
                  {data.audit_notes && ` — ${data.audit_notes}`}
                </span>
              </div>
              <div className="flex items-center gap-1 text-zinc-400 font-mono text-[11px]">
                <Clock className="h-3 w-3" />
                <span>{new Date(data.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
            </div>

            {/* Markdown Report View */}
            <div className="border border-zinc-800 rounded-md bg-zinc-900/30 p-6 md:p-8">
              <div className="prose prose-invert max-w-none text-zinc-300 text-sm leading-relaxed space-y-4">
                <ReactMarkdown
                  components={{
                    h1: ({ children }) => <h1 className="text-lg font-semibold text-zinc-100 border-b border-zinc-800 pb-2 mb-4">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-base font-semibold text-zinc-200 mt-6 mb-3">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-sm font-medium text-zinc-300 mt-4 mb-2">{children}</h3>,
                    p: ({ children }) => <p className="mb-3 text-zinc-300 leading-normal">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc pl-5 mb-4 space-y-1 text-zinc-400">{children}</ul>,
                    li: ({ children }) => <li className="text-zinc-300">{children}</li>,
                    strong: ({ children }) => <strong className="text-zinc-100 font-semibold">{children}</strong>,
                  }}
                >
                  {data.final_report}
                </ReactMarkdown>
              </div>
            </div>

          </div>
        )}

      </div>
    </main>
  );
}