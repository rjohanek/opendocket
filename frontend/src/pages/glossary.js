import { useState } from "react";
import { BookOpen, Search } from "lucide-react";
import Layout from "../components/Layout";
import { useGlossary } from "../hooks/useAPI";

const CONFIDENCE_COLORS = {
  confirmed: "bg-green-100 text-green-700",
  high: "bg-blue-100 text-blue-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-gray-100 text-gray-600",
};

export default function GlossaryPage() {
  const [search, setSearch] = useState("");
  const [confidence, setConfidence] = useState("");
  const [sort, setSort] = useState("occurrences");

  const params = { sort, limit: 200 };
  if (search) params.q = search;
  if (confidence) params.confidence = confidence;

  const { data, isLoading } = useGlossary(params);

  return (
    <Layout>
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-indigo-600" /> Jargon & Code Word Glossary
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          Community-decoded terms found across documents. Confidence levels reflect sourcing strength.
        </p>

        <div className="flex items-center gap-4 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input type="text" placeholder="Search terms..."
              value={search} onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          </div>
          <select value={confidence} onChange={(e) => setConfidence(e.target.value)}
            className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600">
            <option value="">All Confidence</option>
            <option value="confirmed">Confirmed</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select value={sort} onChange={(e) => setSort(e.target.value)}
            className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600">
            <option value="occurrences">Sort: Occurrences</option>
            <option value="term">Sort: Alphabetical</option>
            <option value="confidence">Sort: Confidence</option>
          </select>
        </div>

        {isLoading && <p className="text-gray-400 text-center py-8">Loading...</p>}

        <div className="overflow-hidden rounded-lg border border-gray-200">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-600">Term</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Decoded Meaning</th>
                <th className="text-center px-4 py-3 font-medium text-gray-600">Confidence</th>
                <th className="text-center px-4 py-3 font-medium text-gray-600">Occurrences</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Sources</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(data?.terms || []).map((t) => (
                <tr key={t.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono font-bold text-amber-700">&quot;{t.term}&quot;</td>
                  <td className="px-4 py-3 text-gray-700">{t.decoded_meaning}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${CONFIDENCE_COLORS[t.confidence] || CONFIDENCE_COLORS.low}`}>
                      {t.confidence}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center font-mono text-gray-600">{t.occurrences}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {(t.external_sources || []).join(", ") || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {data?.terms?.length === 0 && (
          <p className="text-gray-400 text-sm text-center py-8">No glossary terms found.</p>
        )}
      </div>
    </Layout>
  );
}
