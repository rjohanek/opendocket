import { useState } from "react";
import Link from "next/link";
import { Clock, PlusCircle, XCircle, RefreshCw } from "lucide-react";
import Layout from "../components/Layout";
import { useChangeFeed } from "../hooks/useAPI";

const ACTION_ICONS = {
  added: PlusCircle,
  removed: XCircle,
  modified: RefreshCw,
  restored: RefreshCw,
};

const ACTION_COLORS = {
  added: "bg-green-50 text-green-700 border-green-200",
  removed: "bg-red-50 text-red-700 border-red-200",
  modified: "bg-amber-50 text-amber-700 border-amber-200",
  restored: "bg-blue-50 text-blue-700 border-blue-200",
};

export default function ChangesPage() {
  const [filter, setFilter] = useState("");
  const params = { limit: 100 };
  if (filter) params.action = filter;

  const { data, isLoading } = useChangeFeed(params);

  return (
    <Layout>
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1 flex items-center gap-2">
          <Clock className="w-5 h-5 text-indigo-600" /> Document Change Log
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          Every addition, removal, and modification is tracked automatically
        </p>

        <div className="flex gap-2 mb-4">
          {["", "added", "removed", "modified", "restored"].map((f) => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs rounded-full font-medium transition-colors ${
                filter === f ? "bg-indigo-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}>
              {f === "" ? "All" : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {isLoading && <p className="text-gray-400 text-center py-8">Loading...</p>}

        <div className="space-y-2">
          {(data?.changes || []).map((change) => {
            const Icon = ACTION_ICONS[change.action] || Clock;
            const color = ACTION_COLORS[change.action] || "bg-gray-50 text-gray-700";
            return (
              <div key={change.id} className={`flex items-start gap-3 p-4 rounded-lg border ${color}`}>
                <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Link href={`/documents/${encodeURIComponent(change.doc_id)}`}
                      className="font-mono text-sm font-bold text-indigo-600 hover:underline">
                      {change.doc_id}
                    </Link>
                    <span className="text-xs font-medium uppercase">{change.action}</span>
                    <span className="text-xs opacity-75">{change.timestamp}</span>
                  </div>
                  {change.doc_title && (
                    <p className="text-sm mt-0.5 opacity-90">{change.doc_title}</p>
                  )}
                  {change.note && (
                    <p className="text-xs mt-1 opacity-75">{change.note}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {data?.changes?.length === 0 && (
          <p className="text-gray-400 text-sm text-center py-8">No changes recorded yet.</p>
        )}
      </div>
    </Layout>
  );
}
