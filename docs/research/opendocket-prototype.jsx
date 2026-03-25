import { useState, useMemo } from "react";
import { Search, FileText, MessageSquare, TrendingUp, Clock, ExternalLink, AlertTriangle, Eye, ChevronDown, ChevronUp, Filter, BarChart3, Users, Globe, BookOpen, Hash, ArrowUpDown, Shield, XCircle, PlusCircle, RefreshCw } from "lucide-react";

// ============================================================
// OPENDOCKET PROTOTYPE
// A unified platform for government document accessibility
// ============================================================

// --- SAMPLE DATA (simulates what the backend would provide) ---

const DOCUMENTS = [
  {
    id: "EFTA-2025-001247",
    title: "Email correspondence between J. Epstein and G. Maxwell regarding travel arrangements",
    category: "Emails",
    dateReleased: "2025-12-19",
    dateRemoved: null,
    pages: 12,
    status: "available",
    aiSummary: "Email chain (June 2003) discussing private flight logistics between New York and Palm Beach. References 'the house' (identified as Epstein's Palm Beach residence) and 'the pilot' (likely Larry Visoski). Mentions upcoming dinner with unnamed 'professor' and arrangements for 'young assistants' — a phrase flagged in multiple other documents as a potential euphemism.",
    entities: ["Jeffrey Epstein", "Ghislaine Maxwell", "Larry Visoski"],
    jargonTerms: ["the house", "the pilot", "young assistants", "professor"],
    discourseScore: 87,
    mentionCount: 2340,
    relatedDocs: ["EFTA-2025-001248", "EFTA-2025-003891"],
    changeHistory: [
      { date: "2025-12-19", action: "added", note: "Initial DOJ release (Batch 1)" },
      { date: "2026-01-15", action: "removed", note: "Removed by DOJ citing 'victim privacy review'" },
      { date: "2026-01-30", action: "restored", note: "Re-added in Batch 3 release with additional redactions" }
    ]
  },
  {
    id: "EFTA-2025-003891",
    title: "FBI Interview notes — Witness 14 testimony regarding recruitment patterns",
    category: "FBI Records",
    dateReleased: "2026-01-30",
    dateRemoved: null,
    pages: 34,
    status: "available",
    aiSummary: "Detailed FBI interview notes from 2006 with a witness describing recruitment methods at a Palm Beach high school. Witness describes being approached by an older student who offered 'massage work' for a wealthy man. Contains references to 'the scheduler' (believed to be Sarah Kellen) and a network of recruiters operating through schools and shopping malls.",
    entities: ["Sarah Kellen", "FBI Agent Rodriguez", "Witness 14"],
    jargonTerms: ["massage work", "the scheduler", "modeling opportunity"],
    discourseScore: 94,
    mentionCount: 5120,
    relatedDocs: ["EFTA-2025-001247", "EFTA-2025-007823"],
    changeHistory: [
      { date: "2026-01-30", action: "added", note: "Released in Batch 3" }
    ]
  },
  {
    id: "EFTA-2025-007823",
    title: "Flight log entries — Aircraft N908JE, January-March 2002",
    category: "Flight Records",
    dateReleased: "2025-12-19",
    dateRemoved: "2026-02-10",
    pages: 8,
    status: "removed",
    aiSummary: "Partial flight manifest for Epstein's Boeing 727 (tail number N908JE, known publicly as 'the Lolita Express'). Covers 14 flights between Teterboro, NJ and various destinations. Passenger lists include initials and partial names — community analysis has identified several as public figures. Document removed by DOJ on Feb 10, 2026; preserved copy available via COURIER archive.",
    entities: ["Jeffrey Epstein", "Multiple unnamed passengers"],
    jargonTerms: ["N908JE", "Lolita Express", "JE", "GM", "SK"],
    discourseScore: 99,
    mentionCount: 12800,
    relatedDocs: ["EFTA-2025-001247", "EFTA-2026-012001"],
    changeHistory: [
      { date: "2025-12-19", action: "added", note: "Initial DOJ release (Batch 1)" },
      { date: "2026-02-10", action: "removed", note: "Removed by DOJ — no public explanation provided" }
    ]
  },
  {
    id: "EFTA-2026-012001",
    title: "Ghislaine Maxwell deposition transcript — sealed portions (partial)",
    category: "Legal Documents",
    dateReleased: "2026-02-28",
    dateRemoved: null,
    pages: 156,
    status: "available",
    aiSummary: "Previously sealed portions of Ghislaine Maxwell's civil deposition from Giuffre v. Maxwell. Contains testimony about the organizational structure of Epstein's network, property management across multiple residences, and Maxwell's self-described role as 'head of household.' Heavy redactions remain on sections discussing specific individuals. References 'the black book' (Epstein's contact directory) and 'the schedule' (daily appointment system).",
    entities: ["Ghislaine Maxwell", "Virginia Giuffre", "Attorney Sigrid McCawley"],
    jargonTerms: ["head of household", "the black book", "the schedule", "the island"],
    discourseScore: 96,
    mentionCount: 8900,
    relatedDocs: ["EFTA-2025-007823", "EFTA-2025-003891"],
    changeHistory: [
      { date: "2026-02-28", action: "added", note: "Released in Batch 5 (sealed materials)" }
    ]
  },
  {
    id: "EFTA-2025-002156",
    title: "Property records and financial transfers — Zorro Ranch, NM",
    category: "Financial Records",
    dateReleased: "2025-12-19",
    dateRemoved: null,
    pages: 22,
    status: "available",
    aiSummary: "Documentation of property transactions for Epstein's Zorro Ranch in Stanley, New Mexico. Includes LLC structures ('Zorro Trust'), transfer documents, and correspondence about ranch operations. References to 'scientific research' and 'educational programs' that investigators flagged as potential fronts. Contains names of local officials involved in permitting.",
    entities: ["Zorro Trust LLC", "NM Land Commissioner"],
    jargonTerms: ["Zorro Trust", "scientific research", "educational programs"],
    discourseScore: 62,
    mentionCount: 890,
    relatedDocs: ["EFTA-2026-012001"],
    changeHistory: [
      { date: "2025-12-19", action: "added", note: "Initial DOJ release (Batch 1)" }
    ]
  },
  {
    id: "EFTA-2026-015443",
    title: "Blanche-Maxwell recorded conversation transcript — Session 3",
    category: "Transcripts",
    dateReleased: "2026-03-10",
    dateRemoved: null,
    pages: 48,
    status: "available",
    aiSummary: "Third session of recorded conversations between Deputy AG Todd Blanche and Ghislaine Maxwell. Discussion covers Maxwell's knowledge of financial arrangements and offshore accounts. Maxwell references 'the foundation' (likely referring to one of several Epstein-connected foundations) and names individuals described as 'benefactors.' Independent transcription by COURIER differs from DOJ version in several key passages.",
    entities: ["Todd Blanche", "Ghislaine Maxwell"],
    jargonTerms: ["the foundation", "benefactors", "the arrangement"],
    discourseScore: 91,
    mentionCount: 6200,
    relatedDocs: ["EFTA-2026-012001", "EFTA-2025-002156"],
    changeHistory: [
      { date: "2026-03-10", action: "added", note: "Released in Batch 7" }
    ]
  }
];

const DISCOURSE_DATA = {
  "EFTA-2025-007823": {
    summary: "This document has generated the most public discussion of any single release, largely because it contains partial flight manifests for Epstein's Boeing 727. Online analysis has focused on decoding passenger initials, with Reddit communities cross-referencing initials against known associates from the 'black book.' Several news outlets have published investigations based on this document, and its removal by the DOJ on Feb 10 sparked significant controversy and accusations of a cover-up.",
    sources: [
      { platform: "Reddit", subreddit: "r/EpsteinFiles", title: "Flight log analysis: decoded initials from EFTA-2025-007823", url: "#", upvotes: 14200, date: "2026-01-02", type: "social" },
      { platform: "News", outlet: "The Guardian", title: "Epstein flight logs reveal patterns of travel to private island", url: "#", date: "2026-01-05", type: "news" },
      { platform: "YouTube", channel: "Legal Eagle", title: "Breaking Down the Epstein Flight Logs — What They Actually Show", url: "#", views: 2100000, date: "2026-01-08", type: "social" },
      { platform: "News", outlet: "CBS News", title: "DOJ removes flight log documents without explanation", url: "#", date: "2026-02-11", type: "news" },
      { platform: "X/Twitter", handle: "@technosocialist", title: "Thread: Why the DOJ removed document EFTA-2025-007823 and what was in it", url: "#", likes: 89000, date: "2026-02-12", type: "social" },
      { platform: "News", outlet: "NPR", title: "Removed Epstein documents included flight records mentioning political figures", url: "#", date: "2026-02-24", type: "news" },
      { platform: "Legal", source: "PACER", title: "Giuffre v. Maxwell — Motion referencing flight logs as Exhibit 14", url: "#", date: "2023-08-15", type: "legal" },
      { platform: "Reddit", subreddit: "r/conspiracy", title: "Comparison: What changed between original and re-released flight logs", url: "#", upvotes: 8900, date: "2026-02-15", type: "social" }
    ],
    coMentioned: ["EFTA-2026-012001", "EFTA-2025-001247"],
    heatTrend: [12, 45, 89, 78, 156, 234, 312, 189, 145, 167, 290, 410, 380]
  },
  "EFTA-2025-001247": {
    summary: "This email chain has drawn attention for its use of coded language. Reddit users and independent journalists have compiled analyses suggesting 'young assistants' is a euphemism found across multiple documents. The document's temporary removal and subsequent re-release with additional redactions has been cited as evidence of selective censorship.",
    sources: [
      { platform: "Reddit", subreddit: "r/EpsteinFiles", title: "Coded language analysis: 'young assistants' appears in 47 documents", url: "#", upvotes: 6700, date: "2026-01-22", type: "social" },
      { platform: "News", outlet: "Axios", title: "How community tools are decoding Epstein document jargon", url: "#", date: "2026-01-25", type: "news" },
      { platform: "YouTube", channel: "TLDR News", title: "The coded language in Epstein's emails, explained", url: "#", views: 890000, date: "2026-02-01", type: "social" },
      { platform: "News", outlet: "Al Jazeera", title: "Visual guide: Navigating the Epstein files", url: "#", date: "2026-02-10", type: "news" }
    ],
    coMentioned: ["EFTA-2025-003891", "EFTA-2025-007823"],
    heatTrend: [5, 12, 34, 67, 89, 56, 45, 78, 90, 65, 45, 38, 42]
  },
  "EFTA-2025-003891": {
    summary: "The FBI interview notes have become central to public understanding of Epstein's recruitment methods. Witness 14's testimony has been extensively discussed in legal analysis communities and by survivor advocacy groups. The document has been cross-referenced with school records and news reports from Palm Beach County.",
    sources: [
      { platform: "Reddit", subreddit: "r/TrueCrime", title: "Witness 14 testimony reveals organized recruitment at Palm Beach schools", url: "#", upvotes: 11300, date: "2026-02-02", type: "social" },
      { platform: "News", outlet: "Miami Herald", title: "FBI notes detail Epstein recruitment network at local schools", url: "#", date: "2026-02-05", type: "news" },
      { platform: "Legal", source: "Palm Beach County Court", title: "State v. Epstein — Original 2006 case files cross-referencing Witness 14", url: "#", date: "2008-06-30", type: "legal" },
      { platform: "News", outlet: "Reuters Institute", title: "How newsrooms are digging into the Epstein files", url: "#", date: "2026-03-01", type: "news" }
    ],
    coMentioned: ["EFTA-2025-001247", "EFTA-2026-012001"],
    heatTrend: [0, 0, 0, 0, 0, 8, 45, 120, 95, 78, 65, 55, 50]
  },
  "EFTA-2026-012001": {
    summary: "The unsealed Maxwell deposition has generated intense scrutiny, particularly around her description of being 'head of household' and references to 'the black book.' Legal analysts have compared redacted sections to previously leaked versions, finding discrepancies. The document is frequently discussed alongside the flight logs and Blanche-Maxwell transcripts.",
    sources: [
      { platform: "Reddit", subreddit: "r/EpsteinFiles", title: "Maxwell deposition: comparing redacted vs leaked versions", url: "#", upvotes: 9400, date: "2026-03-02", type: "social" },
      { platform: "News", outlet: "New York Times", title: "Maxwell deposition reveals organizational structure of Epstein operation", url: "#", date: "2026-03-03", type: "news" },
      { platform: "YouTube", channel: "Law & Crime", title: "LIVE analysis: Maxwell deposition unsealed portions", url: "#", views: 3400000, date: "2026-03-01", type: "social" },
      { platform: "Legal", source: "SDNY Court Filing", title: "USA v. Maxwell — Government exhibit list referencing deposition", url: "#", date: "2021-11-29", type: "legal" },
      { platform: "X/Twitter", handle: "@julie_k_brown", title: "Key takeaways from Maxwell deposition — what the redactions hide", url: "#", likes: 45000, date: "2026-03-02", type: "social" }
    ],
    coMentioned: ["EFTA-2025-007823", "EFTA-2026-015443"],
    heatTrend: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15, 280, 350]
  },
  "EFTA-2025-002156": {
    summary: "The Zorro Ranch financial records have received moderate attention, primarily from investigative journalists examining the LLC structures and potential connections to New Mexico politicians. Discussion has been more muted compared to other documents but is seen as important for understanding Epstein's financial network.",
    sources: [
      { platform: "News", outlet: "Santa Fe Reporter", title: "Epstein's New Mexico connections: what the property records show", url: "#", date: "2026-01-10", type: "news" },
      { platform: "Reddit", subreddit: "r/NewMexico", title: "Local officials named in Epstein ranch documents", url: "#", upvotes: 2300, date: "2026-01-12", type: "social" }
    ],
    coMentioned: ["EFTA-2026-012001"],
    heatTrend: [3, 8, 15, 12, 8, 6, 5, 4, 3, 5, 8, 6, 4]
  },
  "EFTA-2026-015443": {
    summary: "The Blanche-Maxwell transcript has become controversial due to discrepancies between the DOJ's transcription and COURIER's independent version. Discussion has focused on passages where the two versions differ substantively, with some alleging the DOJ version softens Maxwell's statements about unnamed 'benefactors.'",
    sources: [
      { platform: "News", outlet: "COURIER", title: "Our independent transcription of the Blanche-Maxwell tapes differs from DOJ's version", url: "#", date: "2026-03-12", type: "news" },
      { platform: "Reddit", subreddit: "r/EpsteinFiles", title: "Side-by-side: DOJ vs COURIER transcription of Session 3", url: "#", upvotes: 15600, date: "2026-03-13", type: "social" },
      { platform: "YouTube", channel: "Breaking Points", title: "Why do the DOJ's Epstein transcripts differ from independent versions?", url: "#", views: 1800000, date: "2026-03-15", type: "social" },
      { platform: "News", outlet: "The Intercept", title: "Transcript discrepancies raise questions about DOJ handling of Maxwell interviews", url: "#", date: "2026-03-18", type: "news" }
    ],
    coMentioned: ["EFTA-2026-012001", "EFTA-2025-007823"],
    heatTrend: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 45, 280]
  }
};

const JARGON_GLOSSARY = [
  { term: "young assistants", decoded: "Euphemism for underage victims recruited for 'massage' sessions", confidence: "High", occurrences: 47, sources: ["Community analysis", "FBI interview context"] },
  { term: "the house", decoded: "Epstein's Palm Beach residence at 358 El Brillo Way", confidence: "Confirmed", occurrences: 312, sources: ["Property records", "Court filings"] },
  { term: "the island", decoded: "Little St. James, USVI — Epstein's private island", confidence: "Confirmed", occurrences: 189, sources: ["Property records", "Flight logs"] },
  { term: "the pilot", decoded: "Larry Visoski, Epstein's long-time personal pilot", confidence: "Confirmed", occurrences: 67, sources: ["Trial testimony", "FAA records"] },
  { term: "the scheduler", decoded: "Sarah Kellen, who managed Epstein's appointments and recruited victims", confidence: "High", occurrences: 34, sources: ["FBI interviews", "Victim testimony"] },
  { term: "massage work", decoded: "Recruitment euphemism for sexual abuse at Epstein's residences", confidence: "High", occurrences: 89, sources: ["FBI interviews", "Trial testimony"] },
  { term: "modeling opportunity", decoded: "Recruitment pitch used by Epstein's associates to lure victims", confidence: "High", occurrences: 23, sources: ["Victim depositions"] },
  { term: "the black book", decoded: "Epstein's personal contact directory containing ~1,500 names", confidence: "Confirmed", occurrences: 56, sources: ["Court evidence", "Public leak (2015)"] },
  { term: "head of household", decoded: "Maxwell's self-described role managing Epstein's properties and staff", confidence: "Confirmed", occurrences: 12, sources: ["Maxwell deposition"] },
  { term: "N908JE", decoded: "Tail number of Epstein's Boeing 727-31, dubbed 'Lolita Express'", confidence: "Confirmed", occurrences: 44, sources: ["FAA registry", "Flight logs"] },
  { term: "the foundation", decoded: "One of several Epstein-connected entities (e.g., Gratitude America, COUQ Foundation)", confidence: "Medium", occurrences: 28, sources: ["Financial records", "Tax filings"] },
  { term: "benefactors", decoded: "Wealthy individuals connected to Epstein's network; specific identities under investigation", confidence: "Medium", occurrences: 15, sources: ["Maxwell transcripts"] },
  { term: "scientific research", decoded: "Label used for activities at Zorro Ranch; investigators suspect it served as cover", confidence: "Medium", occurrences: 19, sources: ["Property records", "News investigations"] },
  { term: "Zorro Trust", decoded: "LLC used by Epstein to hold Zorro Ranch property in New Mexico", confidence: "Confirmed", occurrences: 8, sources: ["NM property records"] },
  { term: "the arrangement", decoded: "Unclear — appears in Maxwell transcripts referring to financial/logistical structures", confidence: "Low", occurrences: 6, sources: ["Blanche-Maxwell transcripts"] },
];

const CATEGORIES = ["All", "Emails", "FBI Records", "Flight Records", "Legal Documents", "Financial Records", "Transcripts"];
const STATUSES = ["All", "available", "removed"];

// --- MINI SPARKLINE COMPONENT ---
function Sparkline({ data, width = 120, height = 32, color = "#6366f1" }) {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={width} height={height} className="inline-block">
      <polyline fill="none" stroke={color} strokeWidth="2" points={points} />
    </svg>
  );
}

// --- STATUS BADGE ---
function StatusBadge({ status }) {
  if (status === "removed") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
        <XCircle className="w-3 h-3" /> Removed by DOJ
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
      <Eye className="w-3 h-3" /> Available
    </span>
  );
}

// --- CHANGE HISTORY TIMELINE ---
function ChangeTimeline({ history }) {
  return (
    <div className="space-y-2">
      {history.map((event, i) => (
        <div key={i} className="flex items-start gap-3">
          <div className="flex flex-col items-center">
            <div className={`w-3 h-3 rounded-full mt-1 ${
              event.action === "added" ? "bg-green-500" :
              event.action === "removed" ? "bg-red-500" : "bg-blue-500"
            }`} />
            {i < history.length - 1 && <div className="w-0.5 h-6 bg-gray-200" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-gray-500">{event.date}</span>
              <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                event.action === "added" ? "bg-green-50 text-green-700" :
                event.action === "removed" ? "bg-red-50 text-red-700" : "bg-blue-50 text-blue-700"
              }`}>
                {event.action === "added" ? <PlusCircle className="w-3 h-3 inline mr-1" /> :
                 event.action === "removed" ? <XCircle className="w-3 h-3 inline mr-1" /> :
                 <RefreshCw className="w-3 h-3 inline mr-1" />}
                {event.action}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-0.5">{event.note}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// --- DISCOURSE PANEL ---
function DiscoursePanel({ docId }) {
  const [sourceFilter, setSourceFilter] = useState("all");
  const discourse = DISCOURSE_DATA[docId];
  if (!discourse) return <p className="text-gray-500 text-sm p-4">No discourse data available for this document yet.</p>;

  const filteredSources = sourceFilter === "all" ? discourse.sources : discourse.sources.filter(s => s.type === sourceFilter);

  return (
    <div className="space-y-4">
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-indigo-900 mb-2 flex items-center gap-2">
          <MessageSquare className="w-4 h-4" /> AI Discourse Summary
        </h4>
        <p className="text-sm text-indigo-800 leading-relaxed">{discourse.summary}</p>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-500">Discussion trend (13 weeks):</span>
          <Sparkline data={discourse.heatTrend} color="#6366f1" />
        </div>
        {discourse.coMentioned.length > 0 && (
          <div className="text-xs text-gray-500">
            Often discussed with: {discourse.coMentioned.map(id => (
              <span key={id} className="font-mono text-indigo-600 ml-1">{id}</span>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-2">
        {["all", "news", "social", "legal"].map(f => (
          <button key={f} onClick={() => setSourceFilter(f)}
            className={`px-3 py-1 text-xs rounded-full font-medium transition-colors ${
              sourceFilter === f ? "bg-indigo-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}>
            {f === "all" ? "All Sources" : f === "news" ? "News" : f === "social" ? "Social Media" : "Legal"}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {filteredSources.map((source, i) => (
          <div key={i} className="flex items-start gap-3 p-3 bg-white border border-gray-200 rounded-lg hover:border-indigo-300 transition-colors">
            <div className={`p-1.5 rounded ${
              source.type === "news" ? "bg-blue-100 text-blue-600" :
              source.type === "social" ? "bg-purple-100 text-purple-600" :
              "bg-amber-100 text-amber-600"
            }`}>
              {source.type === "news" ? <Globe className="w-4 h-4" /> :
               source.type === "social" ? <Users className="w-4 h-4" /> :
               <BookOpen className="w-4 h-4" />}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-medium text-gray-400">{source.platform}</span>
                {source.outlet && <span className="text-xs text-gray-500">— {source.outlet}</span>}
                {source.subreddit && <span className="text-xs text-gray-500">— {source.subreddit}</span>}
                {source.channel && <span className="text-xs text-gray-500">— {source.channel}</span>}
                {source.handle && <span className="text-xs text-gray-500">— {source.handle}</span>}
                {source.source && <span className="text-xs text-gray-500">— {source.source}</span>}
              </div>
              <p className="text-sm font-medium text-gray-800 mt-0.5 truncate">{source.title}</p>
              <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                <span>{source.date}</span>
                {source.upvotes && <span>{source.upvotes.toLocaleString()} upvotes</span>}
                {source.views && <span>{source.views.toLocaleString()} views</span>}
                {source.likes && <span>{source.likes.toLocaleString()} likes</span>}
              </div>
            </div>
            <ExternalLink className="w-4 h-4 text-gray-300 flex-shrink-0 mt-1" />
          </div>
        ))}
      </div>
    </div>
  );
}

// --- DOCUMENT DETAIL VIEW ---
function DocumentDetail({ doc, onBack }) {
  const [activeTab, setActiveTab] = useState("summary");

  return (
    <div>
      <button onClick={onBack} className="text-sm text-indigo-600 hover:text-indigo-800 mb-4 flex items-center gap-1">
        &larr; Back to document index
      </button>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className="font-mono text-sm font-bold text-indigo-600">{doc.id}</span>
                <StatusBadge status={doc.status} />
                <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">{doc.category}</span>
              </div>
              <h2 className="text-xl font-semibold text-gray-900">{doc.title}</h2>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                <span className="flex items-center gap-1"><FileText className="w-4 h-4" /> {doc.pages} pages</span>
                <span className="flex items-center gap-1"><Clock className="w-4 h-4" /> Released {doc.dateReleased}</span>
                <span className="flex items-center gap-1"><MessageSquare className="w-4 h-4" /> {doc.mentionCount.toLocaleString()} mentions</span>
              </div>
            </div>
            <div className="text-right flex-shrink-0">
              <div className="text-3xl font-bold text-indigo-600">{doc.discourseScore}</div>
              <div className="text-xs text-gray-400">Discourse Score</div>
            </div>
          </div>

          {doc.status === "removed" && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-800">This document has been removed from the DOJ website</p>
                <p className="text-xs text-red-600 mt-1">Removed on {doc.dateRemoved}. A preserved copy is available via the COURIER archive and this platform's cache.</p>
              </div>
            </div>
          )}
        </div>

        <div className="border-b border-gray-100">
          <nav className="flex">
            {[
              { id: "summary", label: "AI Summary", icon: FileText },
              { id: "discourse", label: "Public Discourse", icon: MessageSquare },
              { id: "history", label: "Change History", icon: Clock },
              { id: "glossary", label: "Jargon Decoder", icon: BookOpen }
            ].map(tab => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}>
                <tab.icon className="w-4 h-4" /> {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === "summary" && (
            <div className="space-y-4">
              <p className="text-gray-700 leading-relaxed">{doc.aiSummary}</p>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Named Entities</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {doc.entities.map(e => (
                      <span key={e} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">{e}</span>
                    ))}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Flagged Terms</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {doc.jargonTerms.map(t => (
                      <span key={t} className="px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded-full font-mono">"{t}"</span>
                    ))}
                  </div>
                </div>
              </div>
              {doc.relatedDocs.length > 0 && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Related Documents</h4>
                  <div className="flex flex-wrap gap-2">
                    {doc.relatedDocs.map(id => (
                      <span key={id} className="font-mono text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded">{id}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          {activeTab === "discourse" && <DiscoursePanel docId={doc.id} />}
          {activeTab === "history" && <ChangeTimeline history={doc.changeHistory} />}
          {activeTab === "glossary" && (
            <div className="space-y-2">
              {JARGON_GLOSSARY.filter(j => doc.jargonTerms.includes(j.term)).map(j => (
                <div key={j.term} className="p-3 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-bold text-amber-700">"{j.term}"</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      j.confidence === "Confirmed" ? "bg-green-100 text-green-700" :
                      j.confidence === "High" ? "bg-blue-100 text-blue-700" :
                      j.confidence === "Medium" ? "bg-yellow-100 text-yellow-700" :
                      "bg-gray-100 text-gray-600"
                    }`}>{j.confidence} confidence</span>
                  </div>
                  <p className="text-sm text-gray-700 mt-1">{j.decoded}</p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                    <span>Found in {j.occurrences} documents</span>
                    <span>Sources: {j.sources.join(", ")}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// --- MAIN APP ---
export default function OpenDocket() {
  const [view, setView] = useState("index"); // index | detail | glossary | trending
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  const [sortBy, setSortBy] = useState("discourse"); // discourse | date | mentions

  const filteredDocs = useMemo(() => {
    let docs = [...DOCUMENTS];
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      docs = docs.filter(d =>
        d.id.toLowerCase().includes(q) ||
        d.title.toLowerCase().includes(q) ||
        d.aiSummary.toLowerCase().includes(q) ||
        d.entities.some(e => e.toLowerCase().includes(q)) ||
        d.jargonTerms.some(t => t.toLowerCase().includes(q))
      );
    }
    if (categoryFilter !== "All") docs = docs.filter(d => d.category === categoryFilter);
    if (statusFilter !== "All") docs = docs.filter(d => d.status === statusFilter);
    docs.sort((a, b) => {
      if (sortBy === "discourse") return b.discourseScore - a.discourseScore;
      if (sortBy === "mentions") return b.mentionCount - a.mentionCount;
      return new Date(b.dateReleased) - new Date(a.dateReleased);
    });
    return docs;
  }, [searchQuery, categoryFilter, statusFilter, sortBy]);

  const stats = useMemo(() => ({
    total: DOCUMENTS.length,
    available: DOCUMENTS.filter(d => d.status === "available").length,
    removed: DOCUMENTS.filter(d => d.status === "removed").length,
    totalMentions: DOCUMENTS.reduce((sum, d) => sum + d.mentionCount, 0),
  }), []);

  const openDoc = (doc) => { setSelectedDoc(doc); setView("detail"); };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* HEADER */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">OpenDocket</h1>
                <p className="text-xs text-gray-500">Government Document Accessibility Platform</p>
              </div>
            </div>
            <nav className="flex items-center gap-1">
              {[
                { id: "index", label: "Document Index", icon: FileText },
                { id: "trending", label: "Trending", icon: TrendingUp },
                { id: "glossary", label: "Jargon Glossary", icon: BookOpen },
              ].map(tab => (
                <button key={tab.id}
                  onClick={() => { setView(tab.id); setSelectedDoc(null); }}
                  className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    (view === tab.id || (view === "detail" && tab.id === "index"))
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                  }`}>
                  <tab.icon className="w-4 h-4" /> {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* STATS BAR */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: "Total Documents", value: stats.total.toLocaleString(), icon: FileText, color: "indigo" },
            { label: "Available", value: stats.available.toLocaleString(), icon: Eye, color: "green" },
            { label: "Removed by DOJ", value: stats.removed.toLocaleString(), icon: XCircle, color: "red" },
            { label: "Total Online Mentions", value: stats.totalMentions.toLocaleString(), icon: MessageSquare, color: "purple" },
          ].map(stat => (
            <div key={stat.label} className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4">
              <div className={`p-2.5 rounded-lg bg-${stat.color}-50`}>
                <stat.icon className={`w-5 h-5 text-${stat.color}-600`} />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                <div className="text-xs text-gray-500">{stat.label}</div>
              </div>
            </div>
          ))}
        </div>

        {/* DOCUMENT INDEX VIEW */}
        {(view === "index") && (
          <div>
            <div className="flex items-center gap-4 mb-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type="text" placeholder="Search by document ID, title, entity, or keyword..."
                  value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
              </div>
              <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}
                className="px-3 py-2.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                {CATEGORIES.map(c => <option key={c} value={c}>{c === "All" ? "All Categories" : c}</option>)}
              </select>
              <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
                className="px-3 py-2.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                {STATUSES.map(s => <option key={s} value={s}>{s === "All" ? "All Statuses" : s === "available" ? "Available" : "Removed"}</option>)}
              </select>
              <select value={sortBy} onChange={e => setSortBy(e.target.value)}
                className="px-3 py-2.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <option value="discourse">Sort: Discourse Score</option>
                <option value="mentions">Sort: Mention Count</option>
                <option value="date">Sort: Release Date</option>
              </select>
            </div>

            <div className="space-y-3">
              {filteredDocs.map(doc => (
                <div key={doc.id} onClick={() => openDoc(doc)}
                  className={`bg-white border rounded-xl p-5 cursor-pointer transition-all hover:shadow-md hover:border-indigo-300 ${
                    doc.status === "removed" ? "border-red-200 bg-red-50/30" : "border-gray-200"
                  }`}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                        <span className="font-mono text-sm font-bold text-indigo-600">{doc.id}</span>
                        <StatusBadge status={doc.status} />
                        <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">{doc.category}</span>
                        {doc.changeHistory.length > 1 && (
                          <span className="text-xs px-2 py-0.5 rounded bg-orange-100 text-orange-700 flex items-center gap-1">
                            <RefreshCw className="w-3 h-3" /> {doc.changeHistory.length} changes
                          </span>
                        )}
                      </div>
                      <h3 className="text-base font-medium text-gray-900 mb-1">{doc.title}</h3>
                      <p className="text-sm text-gray-500 line-clamp-2">{doc.aiSummary}</p>
                      <div className="flex items-center gap-4 mt-2">
                        <span className="text-xs text-gray-400 flex items-center gap-1"><FileText className="w-3 h-3" /> {doc.pages} pages</span>
                        <span className="text-xs text-gray-400 flex items-center gap-1"><Clock className="w-3 h-3" /> {doc.dateReleased}</span>
                        <span className="text-xs text-gray-400 flex items-center gap-1"><MessageSquare className="w-3 h-3" /> {doc.mentionCount.toLocaleString()} mentions</span>
                        <div className="flex items-center gap-1">
                          <span className="text-xs text-gray-400">Trend:</span>
                          <Sparkline data={DISCOURSE_DATA[doc.id]?.heatTrend} width={80} height={20} color={doc.discourseScore > 90 ? "#ef4444" : "#6366f1"} />
                        </div>
                      </div>
                    </div>
                    <div className="text-center flex-shrink-0 pl-4">
                      <div className={`text-2xl font-bold ${
                        doc.discourseScore >= 90 ? "text-red-500" :
                        doc.discourseScore >= 70 ? "text-orange-500" :
                        "text-indigo-500"
                      }`}>{doc.discourseScore}</div>
                      <div className="text-xs text-gray-400">Discourse</div>
                    </div>
                  </div>
                </div>
              ))}
              {filteredDocs.length === 0 && (
                <div className="text-center py-12 text-gray-400">
                  <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No documents match your search criteria</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* DOCUMENT DETAIL VIEW */}
        {view === "detail" && selectedDoc && (
          <DocumentDetail doc={selectedDoc} onBack={() => setView("index")} />
        )}

        {/* TRENDING VIEW */}
        {view === "trending" && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-1 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-indigo-600" /> Most Discussed Documents
              </h2>
              <p className="text-sm text-gray-500 mb-4">Ranked by total online mentions across news, social media, and legal sources</p>
              <div className="space-y-3">
                {[...DOCUMENTS].sort((a, b) => b.mentionCount - a.mentionCount).map((doc, i) => (
                  <div key={doc.id} onClick={() => openDoc(doc)}
                    className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg cursor-pointer hover:bg-indigo-50 transition-colors">
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
                    <div className="flex items-center gap-6 flex-shrink-0">
                      <Sparkline data={DISCOURSE_DATA[doc.id]?.heatTrend} width={100} height={28} color={doc.discourseScore > 90 ? "#ef4444" : "#6366f1"} />
                      <div className="text-right">
                        <div className="text-lg font-bold text-gray-900">{doc.mentionCount.toLocaleString()}</div>
                        <div className="text-xs text-gray-400">mentions</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-1 flex items-center gap-2">
                <Hash className="w-5 h-5 text-indigo-600" /> Document Co-mention Network
              </h2>
              <p className="text-sm text-gray-500 mb-4">Documents frequently discussed together — click any pair to explore</p>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(DISCOURSE_DATA).flatMap(([docId, data]) =>
                  data.coMentioned.map(coId => ({
                    pair: [docId, coId].sort().join(" + "),
                    docs: [docId, coId]
                  }))
                ).filter((item, i, arr) => arr.findIndex(x => x.pair === item.pair) === i)
                .map(({ pair, docs }) => (
                  <div key={pair} className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1 flex items-center gap-2">
                      <span className="font-mono text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded cursor-pointer hover:bg-indigo-100"
                        onClick={() => openDoc(DOCUMENTS.find(d => d.id === docs[0]))}>
                        {docs[0]}
                      </span>
                      <span className="text-xs text-gray-400">&harr;</span>
                      <span className="font-mono text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded cursor-pointer hover:bg-indigo-100"
                        onClick={() => openDoc(DOCUMENTS.find(d => d.id === docs[1]))}>
                        {docs[1]}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* FULL GLOSSARY VIEW */}
        {view === "glossary" && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-1 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-indigo-600" /> Jargon & Code Word Glossary
            </h2>
            <p className="text-sm text-gray-500 mb-4">Community-decoded terms found across Epstein documents. Confidence levels reflect the strength of sourcing.</p>
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
                  {JARGON_GLOSSARY.sort((a, b) => b.occurrences - a.occurrences).map(j => (
                    <tr key={j.term} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono font-bold text-amber-700">"{j.term}"</td>
                      <td className="px-4 py-3 text-gray-700">{j.decoded}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          j.confidence === "Confirmed" ? "bg-green-100 text-green-700" :
                          j.confidence === "High" ? "bg-blue-100 text-blue-700" :
                          j.confidence === "Medium" ? "bg-yellow-100 text-yellow-700" :
                          "bg-gray-100 text-gray-600"
                        }`}>{j.confidence}</span>
                      </td>
                      <td className="px-4 py-3 text-center font-mono text-gray-600">{j.occurrences}</td>
                      <td className="px-4 py-3 text-xs text-gray-500">{j.sources.join(", ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* FOOTER */}
      <footer className="border-t border-gray-200 bg-white mt-12">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between text-xs text-gray-400">
          <span>OpenDocket Prototype — Government Document Accessibility Platform</span>
          <span>Data refreshed: March 25, 2026 | Designed to be generalizable to any government document release</span>
        </div>
      </footer>
    </div>
  );
}
