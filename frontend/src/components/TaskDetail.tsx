import type { Task } from '../types';
import { Charts } from './Charts';

export function TaskDetail({
  task,
  onDelete,
}: {
  task: Task;
  onDelete: () => void;
}) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">
          Research: {task.keyword}
        </h2>
        <button
          onClick={onDelete}
          className="px-3 py-1 text-sm text-red-600 border border-red-300 rounded-lg hover:bg-red-50"
        >
          Delete
        </button>
      </div>

      {task.error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {task.error}
        </div>
      )}

      {task.activities.length > 0 && <Charts activities={task.activities} />}

      {task.report_html ? (
        <div
          className="prose prose-sm max-w-none bg-white p-6 rounded-lg border border-gray-200"
          dangerouslySetInnerHTML={{ __html: task.report_html }}
        />
      ) : task.status === 'completed' ? (
        <div className="text-gray-500">No report generated.</div>
      ) : null}

      {task.activities.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Activities ({task.activities.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-gray-50 text-left">
                  <th className="p-3 border-b font-medium">Title</th>
                  <th className="p-3 border-b font-medium">Price</th>
                  <th className="p-3 border-b font-medium">Rating</th>
                  <th className="p-3 border-b font-medium">Reviews</th>
                  <th className="p-3 border-b font-medium">Duration</th>
                  <th className="p-3 border-b font-medium">Supplier</th>
                </tr>
              </thead>
              <tbody>
                {task.activities.map((a) => (
                  <tr key={a.id} className="border-b hover:bg-gray-50">
                    <td className="p-3 max-w-xs">
                      {a.url ? (
                        <a
                          href={a.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline"
                        >
                          {a.title}
                        </a>
                      ) : (
                        a.title
                      )}
                    </td>
                    <td className="p-3">
                      {a.price != null ? `€${a.price.toFixed(0)}` : '-'}
                    </td>
                    <td className="p-3">{a.rating?.toFixed(1) ?? '-'}</td>
                    <td className="p-3">
                      {a.review_count?.toLocaleString() ?? '-'}
                    </td>
                    <td className="p-3">{a.duration ?? '-'}</td>
                    <td className="p-3 max-w-[150px] truncate">
                      {a.supplier ?? '-'}
                    </td>
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
