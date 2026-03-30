import type { Task, TaskListItem } from './types';

const BASE = import.meta.env.VITE_API_URL || '';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

export const api = {
  createTask: (keyword: string, max_pages = 3) =>
    request<Task>('/api/tasks', {
      method: 'POST',
      body: JSON.stringify({ keyword, max_pages }),
    }),

  listTasks: () => request<TaskListItem[]>('/api/tasks'),

  getTask: (id: number) => request<Task>(`/api/tasks/${id}`),

  deleteTask: (id: number) =>
    request<{ ok: boolean }>(`/api/tasks/${id}`, { method: 'DELETE' }),
};
