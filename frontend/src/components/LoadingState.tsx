function Skeleton({ className }: { className?: string }) {
  return (
    <div className={`rounded-lg bg-muted animate-pulse ${className ?? ""}`} />
  );
}

export default function LoadingState() {
  return (
    <div
      data-testid="loading-skeleton"
      aria-busy="true"
      aria-label="Carregando explicação"
      className="space-y-4"
    >
      {/* Post skeleton */}
      <div className="rounded-2xl border bg-white shadow-sm p-5 space-y-4">
        <div className="flex items-center gap-3">
          <Skeleton className="w-9 h-9 rounded-full" />
          <div className="space-y-1.5">
            <Skeleton className="h-3 w-32" data-testid="skeleton-line" />
            <Skeleton className="h-2.5 w-16" data-testid="skeleton-line" />
          </div>
        </div>
        <Skeleton className="h-3 w-full" data-testid="skeleton-line" />
        <Skeleton className="h-3 w-5/6" data-testid="skeleton-line" />
        <Skeleton className="h-3 w-4/6" data-testid="skeleton-line" />
      </div>

      {/* Context skeleton */}
      <div className="rounded-2xl border bg-white shadow-sm p-5 space-y-4">
        <Skeleton className="h-4 w-24" data-testid="skeleton-line" />
        {[...Array(4)].map((_, i) => (
          <div key={i} className="flex gap-3">
            <Skeleton className="w-5 h-5 rounded-full shrink-0" data-testid="skeleton-line" />
            <div className="flex-1 space-y-1.5">
              <Skeleton className="h-3 w-full" data-testid="skeleton-line" />
              <Skeleton className="h-3 w-4/5" data-testid="skeleton-line" />
            </div>
          </div>
        ))}
      </div>

      <p className="text-center text-xs text-muted-foreground animate-pulse">
        Buscando contexto...
      </p>
    </div>
  );
}
