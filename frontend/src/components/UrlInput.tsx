import { useState } from "react";
import { Loader2, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Props {
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

function isValidBlueskUrl(url: string): boolean {
  return /^https:\/\/bsky\.app\/profile\/.+\/post\/.+/.test(url.trim());
}

export default function UrlInput({ onSubmit, isLoading }: Props) {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit() {
    if (!value.trim()) return;
    if (!isValidBlueskUrl(value)) {
      setError("Use a Bluesky URL: bsky.app/profile/.../post/...");
      return;
    }
    setError(null);
    onSubmit(value.trim());
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleSubmit();
  }

  return (
    <div className="space-y-2 w-full">
      <div className="flex gap-2 shadow-sm">
        <Input
          placeholder="https://bsky.app/profile/.../post/..."
          value={value}
          onChange={(e) => { setValue(e.target.value); if (error) setError(null); }}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          className="flex-1 h-11 bg-white text-sm rounded-xl border-border/70 focus-visible:ring-primary/30"
        />
        <Button
          onClick={handleSubmit}
          disabled={isLoading || !value.trim()}
          className="h-11 px-5 rounded-xl font-medium"
        >
          {isLoading
            ? <Loader2 className="h-4 w-4 animate-spin" />
            : <Search className="h-4 w-4" />
          }
          {isLoading ? "Analyzing..." : "Explain"}
        </Button>
      </div>
      {error && (
        <p className="text-xs text-red-500 pl-1">{error}</p>
      )}
    </div>
  );
}
