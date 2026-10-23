import { ApiError } from "@/lib/api";

/** Friendly message for empty results or a failed API call (rendered instead of crashing the page). */
export default function StatusNote({ error, empty }: { error?: unknown; empty?: string }) {
  if (error) {
    const message = error instanceof ApiError ? error.message : "Something went wrong while loading this section.";
    return (
      <div className="km-empty" role="alert">
        <i className="bi bi-wifi-off d-block mb-2" />
        {message}
      </div>
    );
  }
  return (
    <div className="km-empty">
      <i className="bi bi-basket d-block mb-2" />
      {empty ?? "Nothing to show here yet."}
    </div>
  );
}
