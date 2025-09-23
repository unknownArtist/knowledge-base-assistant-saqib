import { XMarkIcon } from "@heroicons/react/24/solid";

export default function ArticleCard({ article, onAsk, onClose }) {
  if (!article) return null;

  return (
    <div className="w-full max-w-2xl bg-[#343c51] rounded-2xl p-6 shadow-md mt-6 text-gray-300 relative">
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 text-gray-400 hover:text-white"
        aria-label="Close"
      >
        <XMarkIcon className="w-6 h-6" />
      </button>

      {/* Title */}
      <h2 className="text-xl font-semibold text-gray-200 uppercase pr-10">
        {article.title}
      </h2>

      {/* Content preview */}
      <p className="text-gray-200 mt-4 whitespace-pre-line">
        {article.content?.slice(0, 800)}
      </p>

      {/* Meta info */}
      <div className="mt-6 text-sm text-gray-400 space-y-2">
        <div>Author: {article.author_name || "Unknown Author"}</div>
        <div>
          Published:{" "}
          {article.published_date
            ? new Date(article.published_date).toLocaleDateString()
            : "Unknown Date"}
        </div>
        <div>Category: {article.category_name || "Uncategorized"}</div>
      </div>

      {/* Tags */}
      {article.tags?.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-10">
          {article.tags.map((tag, index) => (
            <span
              key={index}
              className="px-2 py-1 rounded-full bg-gray-200 text-[#2a3245] text-xs font-medium"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Ask AI button */}
      <div className="flex justify-end mt-4">
        <button
          onClick={() => onAsk?.(article)}
          className="px-4 py-1.5 bg-[#1e2533] text-gray-200 rounded-full shadow-md hover:bg-[#2a3245] transition"
        >
          Ask AI
        </button>
      </div>
    </div>
  );
}
