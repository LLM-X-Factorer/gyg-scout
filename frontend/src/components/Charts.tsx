import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
} from 'recharts';
import type { Activity } from '../types';

function PriceDistribution({ activities }: { activities: Activity[] }) {
  const prices = activities
    .filter((a) => a.price != null)
    .map((a) => a.price!);

  if (prices.length === 0) return null;

  const min = Math.floor(Math.min(...prices));
  const max = Math.ceil(Math.max(...prices));
  const bucketSize = Math.max(1, Math.ceil((max - min) / 8));

  const buckets: Record<string, number> = {};
  for (let i = min; i <= max; i += bucketSize) {
    const label = `€${i}-${i + bucketSize}`;
    buckets[label] = 0;
  }
  for (const p of prices) {
    const idx = Math.floor((p - min) / bucketSize) * bucketSize + min;
    const label = `€${idx}-${idx + bucketSize}`;
    buckets[label] = (buckets[label] || 0) + 1;
  }

  const data = Object.entries(buckets).map(([range, count]) => ({
    range,
    count,
  }));

  return (
    <div>
      <h4 className="text-sm font-medium text-gray-700 mb-2">
        Price Distribution
      </h4>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="range" tick={{ fontSize: 11 }} />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function PriceVsRating({ activities }: { activities: Activity[] }) {
  const data = activities
    .filter((a) => a.price != null && a.rating != null)
    .map((a) => ({ price: a.price, rating: a.rating, title: a.title }));

  if (data.length === 0) return null;

  return (
    <div>
      <h4 className="text-sm font-medium text-gray-700 mb-2">
        Price vs Rating
      </h4>
      <ResponsiveContainer width="100%" height={200}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="price" name="Price (€)" tick={{ fontSize: 11 }} />
          <YAxis dataKey="rating" name="Rating" domain={[0, 5]} />
          <Tooltip />
          <Scatter data={data} fill="#8b5cf6" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

function RatingDistribution({ activities }: { activities: Activity[] }) {
  const ratings = activities
    .filter((a) => a.rating != null)
    .map((a) => a.rating!);

  if (ratings.length === 0) return null;

  const buckets = [
    { range: '< 3.0', count: 0 },
    { range: '3.0-3.5', count: 0 },
    { range: '3.5-4.0', count: 0 },
    { range: '4.0-4.5', count: 0 },
    { range: '4.5-5.0', count: 0 },
  ];
  for (const r of ratings) {
    if (r < 3) buckets[0].count++;
    else if (r < 3.5) buckets[1].count++;
    else if (r < 4) buckets[2].count++;
    else if (r < 4.5) buckets[3].count++;
    else buckets[4].count++;
  }

  return (
    <div>
      <h4 className="text-sm font-medium text-gray-700 mb-2">
        Rating Distribution
      </h4>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={buckets}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="range" tick={{ fontSize: 11 }} />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function Charts({ activities }: { activities: Activity[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-white rounded-lg border border-gray-200">
      <PriceDistribution activities={activities} />
      <RatingDistribution activities={activities} />
      <PriceVsRating activities={activities} />
    </div>
  );
}
