/**
 * Document Index — main page showing all documents with search and filters.
 */

import { useState } from "react";
import { Search, FileText, Eye, XCircle, MessageSquare } from "lucide-react";
import Layout from "../components/Layout";
import DocumentCard from "../components/DocumentCard";
import { useDocuments, useDocumentStats, useCategories } from "../hooks/useAPI";

export default function IndexPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [sort, setSort] = useState("discourse");

  const params = { sort, limit: 50 };
  if (search) params.q = search;
  if (category) params.category = category;
  if (status) params.status = status;

  const { data, error, isLoading } = useDocuments(params);
  const { data: stats } = useDocumentStats();
  const { data: categories } = useCategories();

  return (
    <Layout>
      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          {
            label: "Total Documents",
            value: stats?.total || 0,
            icon: FileText,
            color: "indigo",
          },
          {
            label: "Available",
            value: stats?.available || 0,
            icon: Eye,
            color: "green",
          },
          {
            label: "Removed",
            value: stats?.removed || 0,
            icon: XCircle,
            color: "red",
          },
          {
            label: "Online Mentions",
            value: stats?.total_mentions || 0,
            icon: MessageSquare,
            color: "purple",
          },
        ].map((stat) => (
          <div
            key={stat.label}
            className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4"
          >
            <div className={`p-2.5 rounded-lg bg-${stat.color}-50`}>
              <stat.icon className={`w-5 h-5 text-${stat.color}-600`} />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {stat.value.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500">{stat.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4 mb-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by document ID, title, entity, or keyword..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="px-3 py-2.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-600"
        >
          <option value="">All Categories</option>
          {(categories || []).map((c) => (
            <option key={c.category} value={c.category}>
              {c.category} ({c.count})
            </option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="px-3 py-2.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-600"
        >
          <option value="">All Statuses</option>
          <option value="available">Available</option>
          <option value="removed">Removed</option>
        </select>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="px-3 py-2.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-600"
        >
          <option value="discourse">Sort: Discourse Score</option>
          <option value="mentions">Sort: Mentions</option>
          <option value="date">Sort: Date</option>
          <option value="title">Sort: Title</option>
        </select>
      </div>

      {/* Document List */}
      {isLoading && (
        <div className="text-center py-12 text-gray-400">Loading documents...</div>
      )}
      {error && (
        <div className="text-center py-12 text-red-500">
          Failed to load documents. Make sure the API is running at{" "}
          {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}.
        </div>
      )}
      {data && (
        <>
          <p className="text-sm text-gray-400 mb-3">
            Showing {data.documents?.length || 0} of {data.total || 0} documents
          </p>
          <div className="space-y-3">
            {(data.documents || []).map((doc) => (
              <DocumentCard key={doc.id} doc={doc} />
            ))}
          </div>
          {data.documents?.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No documents match your search criteria</p>
            </div>
          )}
        </>
      )}
    </Layout>
  );
}
