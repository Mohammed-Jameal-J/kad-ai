"use client";

import { SORT_OPTIONS } from "./filters";

/** Lives inside a GET <Form>; changing it submits the form (client-side navigation). */
export default function SortSelect({ value }: { value?: string }) {
  return (
    <>
      <label htmlFor="sort" className="km-note me-2 mb-0">
        Sort by:
      </label>
      <select
        id="sort"
        name="sort"
        defaultValue={value ?? "relevance"}
        className="form-select form-select-sm w-auto"
        onChange={(e) => e.currentTarget.form?.requestSubmit()}
      >
        {SORT_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <noscript>
        <button type="submit" className="btn btn-sm btn-km ms-2">
          Apply
        </button>
      </noscript>
    </>
  );
}
