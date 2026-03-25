import Link from "next/link";
import { FileText, Clock, MessageSquare, ExternalLink } from "lucide-react";
import StatusBadge from "./StatusBadge";

export default function DocumentCard({ doc }) {
  const scoreColor =
    doc.discourse_score >= 90
      ? "text-red-500"
      : doc.discourse_score >= 70
      ? "text-orange-500"
      : "text-indigo-500";

  return (
    <Link href={`/documents/${encodeURIComponent(doc.id)}`}>
      <div
        className={`bg-white border rounded-xl p-5 cursor-pointer transition-all hover:shadow-md hover:border-indigo-300 ${
          doc.status === "removed" ? "border-red-200 bg-red-50/30" : "border-gray-200"
        }`}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <span className="font-mono text-sm font-bold text-indigo-600">
                {doc.id}
              </span>
              <StatusBadge status={doc.status} />
              {doc.category && (
                <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">
                  {doc.category}
                </span>
              )}
            </div>
            <h3 className="text-base font-medium text-gray-900 mb-1">
              {doc.title}
            </h3>
            {doc.ai_summary && (
              <p className="text-sm text-gray-500 line-clamp-2">{doc.ai_summary}</p>
            )}
            <div className="flex items-center gap-4 mt-2">
              {doc.page_count && (
                <span className="text-xs text-gray-400 flex items-center gap-1">
                  <FileText className="w-3 h-3" /> {doc.page_count} pages
                </span>
              )}
              {doc.date_released && (
                <span className="text-xs text-gray-400 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {doc.date_released}
                </span>
              )}
              <span className="text-xs text-gray-400 flex items-center gap-1">
                <MessageSquare className="w-3 h-3" />{" "}
                {(doc.mention_count || 0).toLocaleString()} mentions
              </span>
              {doc.documentcloud_url && (
                <span className="text-xs text-indigo-500 flex items-center gap-1">
                  <ExternalLink className="w-3 h-3" /> View on DocumentCloud
                </span>
              )}
            </div>
          </div>
          <div className="text-center flex-shrink-0 pl-4">
            <div className={`text-2xl font-bold ${scoreColor}`}>
              {Math.round(doc.discourse_score || 0)}
            </div>
            <div className="text-xs text-gray-400">Discourse</div>
          </div>
        </div>
      </div>
    </Link>
  );
}
