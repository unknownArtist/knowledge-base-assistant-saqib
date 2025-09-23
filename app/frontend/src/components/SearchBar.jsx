// src/components/SearchBar.jsx
import { useEffect, useRef, useState } from "react";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";
import api from "../api/apiClient";
import useDebounce from "../hooks/useDebounce";

export default function SearchBar({ onSelectArticle, onTyping }) {
  const [query, setQuery] = useState("");         // what user types
  const debounced = useDebounce(query, 350);      // wait before calling backend
  const [suggestions, setSuggestions] = useState([]); // list of results
  const [open, setOpen] = useState(false);        // dropdown open/close
  const [loading, setLoading] = useState(false);  // show "Searching…"
  const [activeIndex, setActiveIndex] = useState(-1); // which item is highlighted
  const containerRef = useRef(null);              // to detect click outside

  useEffect(() => {
    if (!debounced || debounced.trim() === "") {
      setSuggestions([]);
      setOpen(false);
      return;
    }

    let canceled = false;
    setLoading(true);

    api.get("/api/v1/search", { params: { query: debounced, limit: 5 } })
      .then((result) => {
        if (canceled) return;
        // Expect res.data = [{id, title, excerpt, ...}, ...]
        setSuggestions(result.data || []);
        setOpen(true);
        setActiveIndex(-1);
      })
      .catch((err) => {
        console.error("Search error:", err);
        setSuggestions([]);
        setOpen(false);
      })
      .finally(() => !canceled && setLoading(false));

    return () => { canceled = true; };
  }, [debounced]);

  // click outside to close
  useEffect(() => {
    function onDocClick(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("click", onDocClick);
    return () => document.removeEventListener("click", onDocClick);
  }, []);

  // keyboard nav: ArrowUp/ArrowDown/Enter/Escape
  function onKeyDown(e) {
    if (!open) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const item = suggestions[activeIndex] || suggestions[0];
      if (item) handleSelect(item);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  function handleSelect(item) {
    setOpen(false);           // close dropdown
    setSuggestions([]);       // clear suggestions
    setLoading(false);        // stop any "Searching…"
    setQuery("");             // clear search box completely

    // notify parent (fetches full article)
    onSelectArticle?.(item.id, item);
  }

  return (
    <div ref={containerRef} className="relative w-full max-w-2xl">

      {/* search input */}

      <div className="flex items-center bg-[#343c51] rounded-xl px-4 py-3 shadow-md">
        <input
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            if (e.target.value.trim()) {
              onTyping?.();   // notify Home when typing starts
            }
          }}
          onKeyDown={onKeyDown}
          placeholder="Search for an article..."
          className="flex-1 bg-transparent outline-none text-gray-300 placeholder-gray-400"
        />

        <button
          className="ml-3 text-gray-300 hover:text-white transition"
          onClick={() => {
            // Treat paper-plane as explicit search trigger; show dropdown results if hidden
            if (!open && query.trim()) {
              // set query to trigger debounced effect quickly by calling API directly:
              setQuery((q) => q); // no-op to ensure debounced runs; or directly call api here if you prefer
            }
          }}
          aria-label="Search"
          title="Search"
        >
          <PaperAirplaneIcon className="w-6 h-6" />
        </button>
      </div>


      {/* dropdown */}
      {open && (
        <ul className="absolute left-0 right-0 mt-2 z-50 max-h-64 overflow-auto rounded-lg bg-[#1f2430] shadow-lg">
          {loading && <li className="px-4 py-3 text-gray-400">Searching…</li>}
          {!loading && suggestions.length === 0 && (
            <li className="px-4 py-3 text-gray-400">No results</li>
          )}
          {!loading &&
            suggestions.map((s, idx) => (
              <li
                key={s.id}
                onClick={() => handleSelect(s)}
                onMouseEnter={() => setActiveIndex(idx)}
                className={`px-4 py-3 cursor-pointer ${idx === activeIndex ? "bg-[#2b3240]" : "hover:bg-[#2b3240]"
                  }`}
              >
                <div className="text-sm text-gray-100 font-medium">{s.title}</div>
                {s.excerpt && (
                  <div className="text-xs text-gray-400 truncate">{s.excerpt}</div>
                )}
              </li>
            ))}
        </ul>
      )}
    </div>
  );
}
