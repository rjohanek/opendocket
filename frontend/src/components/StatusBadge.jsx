import { Eye, XCircle, RefreshCw } from "lucide-react";

export default function StatusBadge({ status }) {
  if (status === "removed") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
        <XCircle className="w-3 h-3" /> Removed by DOJ
      </span>
    );
  }
  if (status === "modified") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
        <RefreshCw className="w-3 h-3" /> Modified
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
      <Eye className="w-3 h-3" /> Available
    </span>
  );
}
