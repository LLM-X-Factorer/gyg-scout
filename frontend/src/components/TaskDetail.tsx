import { useState } from 'react';
import type { Task } from '../types';
import { Charts } from './Charts';

const API_BASE = import.meta.env.VITE_API_URL || '';

export function TaskDetail({
  task,
  onDelete,
}: {
  task: Task;
  onDelete: () => void;
}) {
  const [exporting, setExporting] = useState(false);
  const [activeTab, setActiveTab] = useState<'report' | 'data'>('report');

  const handleExportPdf = async () => {
    setExporting(true);
    try {
      const res = await fetch(`${API_BASE}/api/tasks/${task.id}/export`);
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `gyg-scout-${task.keyword.replace(/\s+/g, '-')}-${task.id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            {task.keyword}
          </h2>
          <p className="text-sm text-gray-500">
            {task.activities.length} activities collected
            {task.completed_at &&
              ` · ${new Date(task.completed_at).toLocaleString()}`}
          </p>
        </div>
        <div className="flex gap-2">
          {task.report_html && (
            <button
              onClick={handleExportPdf}
              disabled={exporting}
              className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {exporting ? 'Exporting...' : 'Download PDF'}
            </button>
          )}
          <button
            onClick={onDelete}
            className="px-3 py-1.5 text-sm text-red-600 border border-red-300 rounded-lg hover:bg-red-50"
          >
            Delete
          </button>
        </div>
      </div>

      {task.error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {task.error}
        </div>
      )}

      {/* Charts */}
      {task.activities.length > 0 && <Charts activities={task.activities} />}

      {/* Tabs */}
      {task.status === 'completed' && (
        <div className="border-b border-gray-200">
          <nav className="flex gap-6">
            <button
              onClick={() => setActiveTab('report')}
              className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'report'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Analysis Report
            </button>
            <button
              onClick={() => setActiveTab('data')}
              className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'data'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Raw Data ({task.activities.length})
            </button>
          </nav>
        </div>
      )}

      {/* Report Tab */}
      {activeTab === 'report' && task.report_html ? (
        <iframe
          srcDoc={task.report_html}
          title="Report"
          className="w-full border border-gray-200 rounded-lg bg-white"
          style={{ minHeight: '800px', height: '80vh' }}
        />
      ) : activeTab === 'report' && task.status === 'completed' ? (
        <div className="text-gray-500 py-8 text-center">
          No report generated.
        </div>
      ) : null}

      {/* Data Tab */}
      {activeTab === 'data' && task.activities.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left border-b border-gray-200">
                  <th className="px-4 py-3 font-medium text-gray-900">Title</th>
                  <th className="px-4 py-3 font-medium text-gray-900 w-20">Price</th>
                  <th className="px-4 py-3 font-medium text-gray-900 w-16">Rating</th>
                  <th className="px-4 py-3 font-medium text-gray-900 w-20">Reviews</th>
                  <th className="px-4 py-3 font-medium text-gray-900 w-28">Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {task.activities.map((a) => (
                  <tr key={a.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      {a.url ? (
                        <a
                          href={a.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline line-clamp-2"
                        >
                          {a.title}
                        </a>
                      ) : (
                        <span className="line-clamp-2">{a.title}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-900 font-medium">
                      {a.price != null ? `¥${a.price.toFixed(0)}` : '-'}
                    </td>
                    <td className="px-4 py-3">
                      {a.rating != null ? (
                        <span
                          className={`font-medium ${
                            a.rating >= 4.5
                              ? 'text-green-700'
                              : a.rating >= 4.0
                                ? 'text-yellow-700'
                                : 'text-red-600'
                          }`}
                        >
                          {a.rating.toFixed(1)}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {a.review_count?.toLocaleString() ?? '-'}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{a.duration ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
