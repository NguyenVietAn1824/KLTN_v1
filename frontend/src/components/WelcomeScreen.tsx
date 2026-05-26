'use client';

const SUGGESTIONS = [
  {
    icon: '🌬️',
    title: 'AQI hiện tại',
    prompt: 'Chỉ số AQI hiện tại ở các quận Hà Nội là bao nhiêu?',
  },
  {
    icon: '📍',
    title: 'Khu vực ô nhiễm nhất',
    prompt: 'Quận nào ở Hà Nội đang có mức độ ô nhiễm cao nhất hiện nay?',
  },
  {
    icon: '📈',
    title: 'Xu hướng tuần qua',
    prompt: 'Cho tôi xem xu hướng chất lượng không khí Hà Nội 7 ngày qua.',
  },
  {
    icon: '✅',
    title: 'Khu vực không khí tốt',
    prompt: 'Khu vực nào ở Hà Nội có chất lượng không khí tốt hôm nay?',
  },
];

interface Props {
  onSuggestionClick: (prompt: string) => void;
}

export default function WelcomeScreen({ onSuggestionClick }: Props) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6">
      <div className="mb-8 flex flex-col items-center gap-3 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
            <path
              d="M9.59 4.59A2 2 0 1111 8H2m10.59 11.41A2 2 0 1014 16H2m15.73-8.27A2.5 2.5 0 1119.5 12H2"
              stroke="#059669"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-semibold text-gray-900">Tôi có thể giúp gì cho bạn?</h1>
        <p className="text-sm text-gray-500">
          Hãy hỏi bất kỳ điều gì về chất lượng không khí ở Hà Nội
        </p>
      </div>

      <div className="grid w-full max-w-2xl grid-cols-2 gap-3">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.title}
            onClick={() => onSuggestionClick(s.prompt)}
            className="rounded-xl border border-gray-200 bg-white p-4 text-left transition hover:border-emerald-300 hover:bg-emerald-50 active:scale-[0.98]"
          >
            <div className="mb-1.5 text-xl">{s.icon}</div>
            <div className="mb-0.5 text-sm font-medium text-gray-900">{s.title}</div>
            <div className="line-clamp-2 text-xs text-gray-500">{s.prompt}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
