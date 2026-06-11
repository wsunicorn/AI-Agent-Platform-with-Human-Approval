/** Knowledge Base Manager page. */

import { Database, MagnifyingGlass, Plus, Trash } from "@phosphor-icons/react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  createDocument,
  deleteDocument,
  fetchDocuments,
  searchKnowledge,
} from "../lib/api";
import { StatusBadge } from "../components/ui/StatusBadge";
import { EmptyState, ErrorState, SkeletonRows } from "../components/ui/States";
import { TimeAgo } from "../components/ui/TimeAgo";
import type { KnowledgeDocument, SearchResult } from "../types/models";

export function KnowledgeBase() {
  const [showCreate, setShowCreate] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null);
  const [searching, setSearching] = useState(false);
  const queryClient = useQueryClient();

  const { data: docs, isLoading, error, refetch } = useQuery({
    queryKey: ["documents"],
    queryFn: () => fetchDocuments(),
  });

  const deleteMut = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const results = await searchKnowledge({ query: searchQuery });
      setSearchResults(results);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-zinc-100">Knowledge Base</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Manage policy documents and reference materials
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 rounded-md bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500"
        >
          <Plus size={16} weight="bold" />
          Add Document
        </button>
      </div>

      {showCreate && (
        <CreateDocForm
          onCreated={() => {
            setShowCreate(false);
            refetch();
          }}
          onCancel={() => setShowCreate(false)}
        />
      )}

      {/* Search Panel */}
      <div className="mb-6 rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
        <h2 className="mb-3 text-sm font-semibold text-zinc-300">
          Search Knowledge Base
        </h2>
        <div className="flex gap-2">
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search policies, procedures, FAQs..."
            className="flex-1 rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:border-teal-500 focus:outline-none"
          />
          <button
            onClick={handleSearch}
            disabled={searching}
            className="flex items-center gap-1.5 rounded-md bg-zinc-700 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-600"
          >
            <MagnifyingGlass size={14} />
            {searching ? "Searching..." : "Search"}
          </button>
        </div>

        {searchResults && (
          <div className="mt-4 space-y-2">
            {searchResults.length === 0 ? (
              <p className="text-sm text-zinc-500">No results found</p>
            ) : (
              searchResults.map((r, i) => (
                <div
                  key={i}
                  className="rounded-md border border-zinc-700 bg-zinc-800/50 p-3"
                >
                  <div className="mb-1 flex items-center gap-2">
                    <span className="text-xs font-medium text-teal-400">
                      Score: {r.score.toFixed(3)}
                    </span>
                    <StatusBadge status={r.method} size="sm" />
                  </div>
                  <p className="text-sm text-zinc-300">{r.chunk_content}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Document List */}
      {isLoading ? (
        <SkeletonRows count={4} />
      ) : error ? (
        <ErrorState message={String(error)} onRetry={refetch} />
      ) : !docs?.length ? (
        <EmptyState
          title="No documents"
          description="Upload policies and reference documents for AI retrieval"
        />
      ) : (
        <div className="space-y-2">
          {docs.map((doc: KnowledgeDocument) => (
            <div
              key={doc.id}
              className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-3"
            >
              <div className="flex items-center gap-3">
                <Database size={18} className="text-zinc-500" />
                <div>
                  <p className="text-sm font-medium text-zinc-200">
                    {doc.title}
                  </p>
                  <div className="mt-0.5 flex items-center gap-2">
                    <StatusBadge status={doc.status} />
                    <span className="text-xs text-zinc-500">
                      {doc.chunk_count ?? 0} chunks
                    </span>
                    <TimeAgo date={doc.created_at} />
                  </div>
                </div>
              </div>
              <button
                onClick={() => deleteMut.mutate(doc.id)}
                className="rounded-md p-2 text-zinc-500 hover:bg-zinc-800 hover:text-red-400"
              >
                <Trash size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CreateDocForm({
  onCreated,
  onCancel,
}: {
  onCreated: () => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [docType, setDocType] = useState("policy");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await createDocument({ title, content, doc_type: docType });
      onCreated();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create document");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-6 rounded-lg border border-zinc-800 bg-zinc-900/70 p-5"
    >
      {error && (
        <div className="mb-4 rounded-md border border-red-900 bg-red-950/40 p-3 text-xs text-red-400">
          {error}
        </div>
      )}
      <div className="space-y-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-400">Title</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:border-teal-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-400">Type</label>
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 focus:border-teal-500 focus:outline-none"
          >
            <option value="policy">Policy</option>
            <option value="faq">FAQ</option>
            <option value="procedure">Procedure</option>
            <option value="reference">Reference</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-400">
            Content (Markdown)
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
            rows={8}
            className="font-mono w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:border-teal-500 focus:outline-none"
          />
        </div>
      </div>
      <div className="mt-4 flex gap-2">
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500 disabled:opacity-50"
        >
          {loading ? "Ingesting..." : "Create & Index"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md bg-zinc-800 px-4 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-700"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
