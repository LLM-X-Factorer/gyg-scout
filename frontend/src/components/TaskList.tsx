import type { TaskListItem, TaskStatus } from '../types';

const STATUS_STYLES: Record<TaskStatus, string> = {
  pending: 'bg-gray-100 text-gray-700',
  scraping: 'bg-yellow-100 text-yellow-800 animate-pulse',
  analyzing: 'bg-purple-100 text-purple-800 animate-pulse',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

const STATUS_LABELS: Record<TaskStatus, string> = {
  pending: 'Pending',
  scraping: 'Scraping...',
  analyzing: 'Analyzing...',
  completed: 'Completed',
  failed: 'Failed',
};

export function TaskList({
  tasks,
  selectedId,
  onSelect,
}: {
  tasks: TaskListItem[];
  selectedId?: number;
  onSelect: (id: number) => void;
}) {
  if (tasks.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        No research tasks yet. Create one above.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <div
          key={task.id}
          onClick={() => onSelect(task.id)}
          className={`p-4 rounded-lg border cursor-pointer transition-colors ${
            selectedId === task.id
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="font-medium text-gray-900">{task.keyword}</div>
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[task.status]}`}
            >
              {STATUS_LABELS[task.status]}
            </span>
          </div>
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
            <span>{task.activity_count} activities</span>
            {task.status === 'scraping' || task.status === 'analyzing' ? (
              <div className="flex-1">
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className="bg-blue-500 h-1.5 rounded-full transition-all"
                    style={{ width: `${task.progress}%` }}
                  />
                </div>
              </div>
            ) : null}
            <span>{new Date(task.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
