import Link from "next/link";
import { useRouter } from "next/router";
import { Shield, FileText, TrendingUp, BookOpen, Clock } from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Documents", icon: FileText },
  { href: "/trending", label: "Trending", icon: TrendingUp },
  { href: "/changes", label: "Change Log", icon: Clock },
  { href: "/glossary", label: "Glossary", icon: BookOpen },
];

export default function Layout({ children }) {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900 leading-tight">OpenDocket</h1>
              <p className="text-xs text-gray-500 leading-tight">
                Government Document Accessibility
              </p>
            </div>
          </Link>

          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const isActive =
                item.href === "/"
                  ? router.pathname === "/"
                  : router.pathname.startsWith(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">{children}</main>

      <footer className="border-t border-gray-200 bg-white mt-12">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between text-xs text-gray-400">
          <span>OpenDocket — Open-source government document accessibility</span>
          <span>
            Powered by DocumentCloud, ChangeDetection.io, ArchiveBox, GDELT,
            and community contributions
          </span>
        </div>
      </footer>
    </div>
  );
}
