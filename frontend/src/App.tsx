import { useState } from "react";
import { AlertCircle } from "lucide-react";
import { explainPost, type ExplainResult } from "@/api/explainer";
import UrlInput from "@/components/UrlInput";
import ResultCard from "@/components/ResultCard";
import LoadingState from "@/components/LoadingState";

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; result: ExplainResult }
  | { status: "error"; message: string };

export default function App() {
  const [state, setState] = useState<State>({ status: "idle" });

  async function handleSubmit(url: string) {
    setState({ status: "loading" });
    try {
      const result = await explainPost(url);
      setState({ status: "success", result });
    } catch (e) {
      setState({ status: "error", message: (e as Error).message });
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Hero header */}
      <div className="bg-gradient-to-b from-blue-50 to-background border-b border-border/50">
        <div className="max-w-2xl mx-auto px-4 pt-14 pb-10 text-center space-y-4">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-primary/10 mb-2">
            <svg viewBox="0 0 24 24" className="w-6 h-6 fill-primary" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/>
            </svg>
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Bluesky Post Explainer
            </h1>
            <p className="mt-2 text-muted-foreground">
              Paste a Bluesky post URL and get AI-powered context in seconds.
            </p>
          </div>
          <div className="pt-2">
            <UrlInput onSubmit={handleSubmit} isLoading={state.status === "loading"} />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        {state.status === "idle" && (
          <div className="text-center py-12 text-muted-foreground text-sm">
            Enter a Bluesky post URL above to get started.
          </div>
        )}

        {state.status === "loading" && <LoadingState />}

        {state.status === "error" && (
          <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-red-700 animate-fade-up">
            <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-sm">Something went wrong</p>
              <p className="text-sm opacity-80 mt-0.5">{state.message}</p>
            </div>
          </div>
        )}

        {state.status === "success" && <ResultCard result={state.result} />}
      </div>
    </div>
  );
}
