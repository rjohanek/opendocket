import Link from "next/link";
import { TrendingUp, Hash } from "lucide-react";
import Layout from "../components/Layout";
import StatusBadge from "../components/StatusBadge";
import { useTrending } from "../hooks/useAPI";

export default function TrendingPage() {
  const { data: trending, isLoading } = useTrending({ limit: 20 });

  return (
    <Layout>
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-indigo-600" /> Most Discussed Documents
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          Ranked by total online mentions across news, social media, and legal sources
        </p>

        {isLoading && <p className="text-gray-400 text-center py-8">Loading...</p>}

        <div className="space-y-3">
          {(trending || []).map((doc, i) => (
            <Link key={doc.id} href={`/documents/${encodeURIComponent(doc.id)}`}>
              <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg cursor-pointer hover:bg-indigo-50 transition-colors">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  i === 0 ? "bg-yellow-400 text-yellow-900" :
                  i === 1 ? "bg-gray-300 text-gray-700" :
                  i === 2 ? "bg-amber-600 text-white" :
                  "bg-gray-100 text-gray-500"
                }`}>{i + 1}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-indigo-600">{doc.id}</span>
                    <StatusBadge status={doc.status} />
                  </div>
                  <p className="text-sm text-gray-700 truncate">{doc.title}</p>
                </div>
                <div className="text-right flex-shrink-0">
                  <div className="text-lg font-bold text-gray-900">{(doc.mention_count || 0).toLocaleString()}</div>
                  <div className="text-xs text-gray-400">mentions</div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </Layout>
  );
}
