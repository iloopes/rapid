import { ExternalLink, Quote } from "lucide-react";
import type { ExplainResult } from "@/api/explainer";

interface Props {
  result: ExplainResult;
}

function AuthorAvatar({ handle }: { handle: string }) {
  const initials = handle.slice(0, 2).toUpperCase();
  return (
    <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
      <span className="text-xs font-bold text-primary">{initials}</span>
    </div>
  );
}

export default function ResultCard({ result }: Props) {
  const { post, bullets, sources } = result;

  return (
    <div className="space-y-4">
      {/* Original post */}
      <div className="animate-fade-up rounded-2xl border bg-white shadow-sm p-5 space-y-3">
        <div className="flex items-center gap-3">
          <AuthorAvatar handle={post.author} />
          <div>
            <p className="text-sm font-semibold text-foreground">@{post.author}</p>
            <p className="text-xs text-muted-foreground">Bluesky</p>
          </div>
        </div>

        {post.image_url && (
          <img
            src={post.image_url}
            alt="Post image"
            className="rounded-xl w-full object-contain bg-muted/30 border border-border/50"
          />
        )}

        <div className="relative pl-4">
          <Quote className="absolute left-0 top-0.5 h-3 w-3 text-muted-foreground/50" />
          <p className="text-sm leading-relaxed text-foreground/90">{post.text}</p>
        </div>
      </div>

      {/* Context bullets */}
      <div className="animate-fade-up animate-fade-up-delay-1 rounded-2xl border bg-white shadow-sm p-5 space-y-4">
        <div className="flex items-center gap-2">
          <div className="w-1 h-5 rounded-full bg-primary" />
          <h2 className="font-semibold text-sm text-foreground">Context</h2>
        </div>

        <ul className="space-y-3">
          {bullets.map((bullet, i) => (
            <li key={i} className="flex gap-3 items-start">
              <span className="shrink-0 w-5 h-5 rounded-full bg-primary/10 text-primary text-[11px] font-bold flex items-center justify-center mt-0.5">
                {i + 1}
              </span>
              <p className="text-sm leading-relaxed text-foreground/85">{bullet}</p>
            </li>
          ))}
        </ul>
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div className="animate-fade-up animate-fade-up-delay-2 rounded-2xl border bg-white shadow-sm p-5 space-y-3">
          <div className="flex items-center gap-2">
            <div className="w-1 h-5 rounded-full bg-muted-foreground/30" />
            <h2 className="font-semibold text-sm text-foreground">Sources</h2>
          </div>
          <div className="space-y-2">
            {sources.map((source, i) => {
              let hostname = source;
              try { hostname = new URL(source).hostname.replace("www.", ""); } catch {}
              return (
                <a
                  key={i}
                  href={source}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors group"
                >
                  <ExternalLink className="h-3.5 w-3.5 shrink-0 group-hover:text-primary" />
                  <span className="truncate">{hostname}</span>
                </a>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
