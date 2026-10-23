"use client";

// Next 16: `retry()` re-fetches and re-renders the failed segment.
export default function Error({ retry }: { error: unknown; retry: () => void }) {
  return (
    <div className="container py-5 text-center">
      <i className="bi bi-exclamation-octagon display-4 text-danger" />
      <h1 className="h3 mt-3">Something went wrong</h1>
      <p className="km-muted">If this keeps happening, please try again in a minute.</p>
      <button type="button" className="btn btn-km" onClick={() => retry()}>
        Try again
      </button>
    </div>
  );
}
