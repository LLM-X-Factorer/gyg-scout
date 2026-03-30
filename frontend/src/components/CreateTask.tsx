import { useState } from 'react';
import { api } from '../api';

export function CreateTask({ onCreated }: { onCreated: () => void }) {
  const [keyword, setKeyword] = useState('');
  const [maxPages, setMaxPages] = useState(3);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword.trim()) return;
    setLoading(true);
    try {
      await api.createTask(keyword.trim(), maxPages);
      setKeyword('');
      onCreated();
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 items-end">
      <div className="flex-1">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Search Keyword
        </label>
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="e.g. paris walking tour"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      <div className="w-24">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Pages
        </label>
        <input
          type="number"
          min={1}
          max={10}
          value={maxPages}
          onChange={(e) => setMaxPages(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      <button
        type="submit"
        disabled={loading || !keyword.trim()}
        className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
      >
        {loading ? 'Creating...' : 'Start Research'}
      </button>
    </form>
  );
}
