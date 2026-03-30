import { useState, useEffect, useCallback } from 'react';
import { api } from './api';
import type { Task, TaskListItem } from './types';
import { CreateTask } from './components/CreateTask';
import { TaskList } from './components/TaskList';
import { TaskDetail } from './components/TaskDetail';
import './App.css';

function App() {
  const [tasks, setTasks] = useState<TaskListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number>();
  const [selectedTask, setSelectedTask] = useState<Task>();
  const [loading, setLoading] = useState(false);

  const refreshTasks = useCallback(async () => {
    const data = await api.listTasks();
    setTasks(data);
  }, []);

  useEffect(() => {
    refreshTasks();
    const interval = setInterval(refreshTasks, 5000);
    return () => clearInterval(interval);
  }, [refreshTasks]);

  useEffect(() => {
    if (!selectedId) {
      setSelectedTask(undefined);
      return;
    }
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      const data = await api.getTask(selectedId);
      if (!cancelled) {
        setSelectedTask(data);
        setLoading(false);
      }
    };
    load();

    const interval = setInterval(async () => {
      const data = await api.getTask(selectedId);
      if (!cancelled) setSelectedTask(data);
    }, 5000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [selectedId]);

  const handleDelete = async () => {
    if (!selectedId) return;
    await api.deleteTask(selectedId);
    setSelectedId(undefined);
    refreshTasks();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            GYG Scout
          </h1>
          <p className="text-sm text-gray-500">
            GetYourGuide Product Research & Competitive Analysis
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        <div className="mb-6 p-4 bg-white rounded-lg border border-gray-200">
          <CreateTask onCreated={refreshTasks} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Research Tasks
            </h2>
            <TaskList
              tasks={tasks}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          </div>

          <div className="lg:col-span-2">
            {loading && !selectedTask ? (
              <div className="flex items-center justify-center py-20 text-gray-400">
                Loading...
              </div>
            ) : selectedTask ? (
              <TaskDetail task={selectedTask} onDelete={handleDelete} />
            ) : (
              <div className="flex items-center justify-center py-20 text-gray-400">
                Select a task to view details
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
