/**
 * Document Detail Page — full view with tabs for summary, discourse,
 * change history, glossary, and embedded DocumentCloud viewer.
 */

import { useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import {
  FileText, MessageSquare, Clock, BookOpen, ExternalLink,
  AlertTriangle, Globe, Users, PlusCircle, XCircle, RefreshCw,
} from "lucide-react";
import Layout from "../../components/Layout";
import StatusBadge from "../../components/StatusBadge";
import { useDocument, useDiscourse, useGlossary } from "../../hooks/useAPI";

const TABS = [
  { id: "summary", label: "AI Summary", icon: FileText },
  { id: "viewer", label: "View Document", icon: Eye },
  { id: "discourse", label: "Public Discourse", icon: MessageSquare },
  { id: "history", label: "Change History", icon: Clock },
  { id: "glossary", label: "Jargon Decoder", icon: BookOpen },
];

// Need to import Eye for the viewer tab
import { Eye } from "lucide-react";

export default function DocumentDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const [activeTab, setActiveTab] = useState("summary");
  const [discourseFilter, setDiscourseFilter] = useState("");

  const { data: doc, error, isLoading } = useDocument(id);
  const { data: discourse } = useDiscourse(id, discourseFilter ? { type: discourseFilter } : {});
  const { data: glossary } = useGlossary();

  if (isLoading) return <Layout><div className="text-center py-12 text-gray-400">Loading...</div></Layout>;
  if (error) return <Layout><div className="text-center py-12 text-red-500">Document not found</div></Layout>;
  if (!doc) return null;

  // Filter glossary to terms in this document
  const docTerms = (glossary?.terms || []).filter(
    (t) => (doc.jargon_terms || []).includes(t.term)
  );

  return (
    <Layout>
      <Link href="/" className="text-sm text-indigo-600 hover:text-indigo-800 mb-4 inline-flex items-center gap-1">
        &larr; Back to document index
      </Link>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className="font-mono text-sm font-bold text-indigo-600">{doc.id}</span>
                <StatusBadge status={doc.status} />
                {doc.category && (
                  <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">{doc.category}</span>
                )}
              </div>
              <h2 className="text-xl font-semibold text-gray-900">{doc.title}</h2>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                {doc.page_count && <span className="flex items-center gap-1"><FileText className="w-4 h-4" /> {doc.page_count} pages</span>}
                {doc.date_released && <span className="flex items-center gap-1"><Clock className="w-4 h-4" /> Released {doc.date_released}</span>}
                <span className="flex items-center gap-1"><MessageSquare className="w-4 h-4" /> {(doc.mention_count || 0).toLocaleString()} mentions</span>
              </div>
            </div>
            <div className="text-right flex-shrink-0">
              <div className="text-3xl font-bold text-indigo-600">{Math.round(doc.discourse_score || 0)}</div>
              <div className="text-xs text-gray-400">Discourse Score</div>
            </div>
          </div>

          {doc.status === "removed" && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-800">This document has been removed from the official source</p>
                <p className="text-xs text-red-600 mt-1">Removed on {doc.date_removed}. A preserved copy is available via ArchiveBox.</p>
              </div>
            </div>
          )}

          {doc.documentcloud_url && (
            <a href={doc.documentcloud_url} target="_blank" rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-2 text-sm text-indigo-600 hover:text-indigo-800">
              <ExternalLink className="w-4 h-4" /> View on DocumentCloud (no download required)
            </a>
          )}
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-100">
          <nav className="flex">
            {TABS.map((tab) => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}>
                <tab.icon className="w-4 h-4" /> {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* Summary Tab */}
          {activeTab === "summary" && (
            <div className="space-y-4">
              <p className="text-gray-700 leading-relaxed">{doc.ai_summary || "No AI summary available yet."}</p>
              <div className="grid grid-cols-2 gap-4">
                {doc.entities?.length > 0 && (
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Named Entities</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {doc.entities.map((e) => (
                        <span key={e} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">{e}</span>
                      ))}
                    </div>
                  </div>
                )}
                {doc.jargon_terms?.length > 0 && (
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Flagged Terms</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {doc.jargon_terms.map((t) => (
                        <span key={t} className="px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded-full font-mono">&quot;{t}&quot;</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* DocumentCloud Viewer Tab */}
          {activeTab === "viewer" && (
            <div>
              {doc.documentcloud_id ? (
                <div className="relative w-full" style={{ paddingBottom: "130%" }}>
                  <iframe
                    src={`https://www.documentcloud.org/documents/${doc.documentcloud_id}/?embed=1&responsive=1`}
                    className="absolute inset-0 w-full h-full border-0"
                    title={doc.title}
                  />
                </div>
              ) : (
                <div className="text-center py-12 text-gray-400">
                  <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>Document not yet uploaded to DocumentCloud.</p>
                  {doc.source_url && (
                    <a href={doc.source_url} className="text-indigo-600 hover:underline text-sm mt-2 inline-block">
                      Download from original source
                    </a>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Discourse Tab */}
          {activeTab === "discourse" && (
            <div className="space-y-4">
              {discourse?.summary?.text && (
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-indigo-900 mb-2 flex items-center gap-2">
                    <MessageSquare className="w-4 h-4" /> AI Discourse Summary
                  </h4>
                  <p className="text-sm text-indigo-800 leading-relaxed">{discourse.summary.text}</p>
                  <p className="text-xs text-indigo-500 mt-2">
                    Based on {discourse.summary.source_count} sources — Generated {discourse.summary.generated_at}
                  </p>
                </div>
              )}

              <div className="flex gap-2">
                {["", "news", "social", "legal"].map((f) => (
                  <button key={f} onClick={() => setDiscourseFilter(f)}
                    className={`px-3 py-1 text-xs rounded-full font-medium transition-colors ${
                      discourseFilter === f ? "bg-indigo-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}>
                    {f === "" ? "All Sources" : f === "news" ? "News" : f === "social" ? "Social Media" : "Legal"}
                  </button>
                ))}
              </div>

              <div className="space-y-2">
                {(discourse?.items || []).map((item) => (
                  <a key={item.id} href={item.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-start gap-3 p-3 bg-white border border-gray-200 rounded-lg hover:border-indigo-300 transition-colors block">
                    <div className={`p-1.5 rounded ${
                      item.type === "news" ? "bg-blue-100 text-blue-600" :
                      item.type === "social" ? "bg-purple-100 text-purple-600" :
                      "bg-amber-100 text-amber-600"
                    }`}>
                      {item.type === "news" ? <Globe className="w-4 h-4" /> :
                       item.type === "social" ? <Users className="w-4 h-4" /> :
                       <BookOpen className="w-4 h-4" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-gray-400">{item.platform}</span>
                        {item.source_name && <span className="text-xs text-gray-500">— {item.source_name}</span>}
                      </div>
                      <p className="text-sm font-medium text-gray-800 mt-0.5 truncate">{item.title}</p>
                      <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                        {item.date && <span>{item.date}</span>}
                        {item.engagement_score > 0 && <span>{item.engagement_score.toLocaleString()} engagement</span>}
                      </div>
                    </div>
                    <ExternalLink className="w-4 h-4 text-gray-300 flex-shrink-0 mt-1" />
                  </a>
                ))}
                {discourse?.items?.length === 0 && (
                  <p className="text-gray-400 text-sm text-center py-8">No discourse items found for this document.</p>
                )}
              </div>
            </div>
          )}

          {/* Change History Tab */}
          {activeTab === "history" && (
            <div className="space-y-3">
              {(doc.change_history || []).map((event, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="flex flex-col items-center">
                    <div className={`w-3 h-3 rounded-full mt-1 ${
                      event.action === "added" ? "bg-green-500" :
                      event.action === "removed" ? "bg-red-500" :
                      event.action === "restored" ? "bg-blue-500" : "bg-amber-500"
                    }`} />
                    {i < (doc.change_history || []).length - 1 && <div className="w-0.5 h-8 bg-gray-200" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-gray-500">{event.timestamp}</span>
                      <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                        event.action === "added" ? "bg-green-50 text-green-700" :
                        event.action === "removed" ? "bg-red-50 text-red-700" :
                        "bg-blue-50 text-blue-700"
                      }`}>
                        {event.action === "added" && <PlusCircle className="w-3 h-3 inline mr-1" />}
                        {event.action === "removed" && <XCircle className="w-3 h-3 inline mr-1" />}
                        {event.action === "restored" && <RefreshCw className="w-3 h-3 inline mr-1" />}
                        {event.action}
                      </span>
                      <span className="text-xs text-gray-400">via {event.detected_by}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-0.5">{event.note}</p>
                  </div>
                </div>
              ))}
              {(!doc.change_history || doc.change_history.length === 0) && (
                <p className="text-gray-400 text-sm text-center py-8">No change history recorded yet.</p>
              )}
            </div>
          )}

          {/* Glossary Tab */}
          {activeTab === "glossary" && (
            <div className="space-y-2">
              {docTerms.length > 0 ? docTerms.map((t) => (
                <div key={t.id} className="p-3 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-bold text-amber-700">&quot;{t.term}&quot;</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      t.confidence === "confirmed" ? "bg-green-100 text-green-700" :
                      t.confidence === "high" ? "bg-blue-100 text-blue-700" :
                      t.confidence === "medium" ? "bg-yellow-100 text-yellow-700" :
                      "bg-gray-100 text-gray-600"
                    }`}>{t.confidence}</span>
                  </div>
                  <p className="text-sm text-gray-700 mt-1">{t.decoded_meaning}</p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                    <span>Found in {t.occurrences} documents</span>
                  </div>
                </div>
              )) : (
                <p className="text-gray-400 text-sm text-center py-8">
                  No flagged jargon terms in this document. Terms are detected automatically and can be proposed by the community.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
