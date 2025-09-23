// src/components/SearchBar.jsx
import { useEffect, useRef, useState } from "react";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";
import api from "../api/apiClient";
import useDebounce from "../hooks/useDebounce";

export default function SearchBar({ onSelectArticle, onTyping }) {
  const [query, setQuery] = useState("");
  const debounced = useDebounce(query, 350);
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const containerRef = useRef(null);

  // ✅ fetch categories when component mounts
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await api.get("/api/v1/categories");
        setCategories(res.data || []);
      } catch (err) {
        console.error("Failed to load categories:", err);
      }
    };

    fetchCategories();
  }, []);

  // ✅ search articles (filtered if category is chosen)
  useEffect(() => {
    if (!debounced || debounced.trim() === "") {
      setSuggestions([]);
      setOpen(false);
      return;
    }

    let canceled = false;

    const searchArticles = async () => {
      setLoading(true);
      try {
        const params = { query: debounced, limit: 5 };
        if (selectedCategory) {
          params.category = selectedCategory;
        }

        const result = await api.get("/api/v1/search", { params });
        if (canceled) return;

        setSuggestions(result.data || []);
        setOpen(true);
        setActiveIndex(-1);
      } catch (err) {
        console.error("Search error:", err);
        setSuggestions([]);
        setOpen(false);
      } finally {
        if (!canceled) setLoading(false);
      }
    };

    searchArticles();

    return () => {
      canceled = true;
    };
  }, [debounced, selectedCategory]);

  // click outside
  useEffect(() => {
    function onDocClick(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("click", onDocClick);
    return () => document.removeEventListener("click", onDocClick);
  }, []);

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
    setOpen(false);
    setSuggestions([]);
    setLoading(false);
    setQuery("");
    onSelectArticle?.(item.id, item);
  }

  return (
    <div ref={containerRef} className="relative w-full max-w-2xl space-y-2">

      {/* wrapper for search bar + category dropdown side by side */}
      <div className="flex items-center gap-3">
        {/* search bar */}
        <div className="flex flex-1 items-center bg-[#343c51] rounded-xl px-4 py-3 shadow-md">
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              if (e.target.value.trim()) {
                onTyping?.();
              }
            }}
            onKeyDown={onKeyDown}
            placeholder="Search for an article..."
            className="flex-1 bg-transparent outline-none text-gray-300 placeholder-gray-400"
          />

          <button
            className="ml-3 text-gray-300 hover:text-white transition"
            onClick={() => {
              if (!open && query.trim()) {
                setQuery((q) => q);
              }
            }}
          >
            <PaperAirplaneIcon className="w-6 h-6" />
          </button>
        </div>

        {/* category dropdown */}
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="bg-[#2a3245] text-gray-300 px-3 py-3 rounded-lg outline-none shadow-md
               appearance-none pr-8 font-medium text-sm"
          style={{
            backgroundImage:
              "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' fill='white' viewBox='0 0 20 20'><path d='M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 011.08 1.04l-4.25 4.25a.75.75 0 01-1.08 0L5.21 8.27a.75.75 0 01.02-1.06z'/></svg>\")",
            backgroundRepeat: "no-repeat",
            backgroundPosition: "right 0.6rem center",
            backgroundSize: "1.2rem",
          }}
        >
          <option value="">All Categories</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.name}>
              {cat.name}
            </option>
          ))}
        </select>
      </div>

      {/* dropdown results */}
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
                className={`px-4 py-3 cursor-pointer ${
                  idx === activeIndex
                    ? "bg-[#2b3240]"
                    : "hover:bg-[#2b3240]"
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
