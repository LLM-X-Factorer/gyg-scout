export interface Activity {
  id: number;
  title: string;
  url?: string;
  price?: number;
  currency?: string;
  rating?: number;
  review_count?: number;
  supplier?: string;
  duration?: string;
  description?: string;
  highlights?: string[];
  includes?: string[];
  excludes?: string[];
  cancellation_policy?: string;
  image_url?: string;
}

export type TaskStatus = 'pending' | 'scraping' | 'analyzing' | 'completed' | 'failed';

export interface Task {
  id: number;
  keyword: string;
  status: TaskStatus;
  max_pages: number;
  progress: number;
  error?: string;
  report_markdown?: string;
  report_html?: string;
  created_at: string;
  completed_at?: string;
  activities: Activity[];
}

export interface TaskListItem {
  id: number;
  keyword: string;
  status: TaskStatus;
  progress: number;
  activity_count: number;
  created_at: string;
  completed_at?: string;
}
