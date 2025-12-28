'use client';

export interface TemperatureInfoCardProps {
  icon: string;
  title: string;
  description: string;
  criteria: string[];
  color: string; // e.g. "from-blue-100/80 to-blue-200/80"
}

export default function TemperatureInfoCard({
  icon,
  title,
  description,
  criteria,
  color,
}: TemperatureInfoCardProps) {
  return (
    <div
      className={`rounded-2xl p-6 bg-gradient-to-br ${color} border border-white/50 shadow-md`}
    >
      <div className="flex items-center gap-3 mb-4">
        <span className="text-3xl">{icon}</span>
        <h3 className="text-xl font-bold text-slate-800">{title}</h3>
      </div>

      <p className="text-slate-700 mb-4 leading-relaxed">{description}</p>

      <ul className="list-disc list-inside space-y-1 text-sm text-slate-600">
        {criteria.map((item, idx) => (
          <li key={idx}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
