'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

interface Props {
  onSend: (message: string) => void;
  isLoading: boolean;
}

export default function InputBar({ onSend, isLoading }: Props) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  }, [value]);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [value, isLoading, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const canSend = value.trim().length > 0 && !isLoading;

  return (
    <div className="flex-shrink-0 px-4 pb-5 pt-2">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-3 rounded-2xl border border-gray-300 bg-white px-4 py-3 shadow-sm transition focus-within:border-emerald-500 focus-within:ring-1 focus-within:ring-emerald-500">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Hỏi về chất lượng không khí ở Hà Nội…"
            rows={1}
            disabled={isLoading}
            className="flex-1 resize-none bg-transparent text-sm leading-relaxed text-gray-900 placeholder:text-gray-400 focus:outline-none disabled:opacity-50"
            style={{ maxHeight: '200px' }}
          />
          <button
            onClick={handleSend}
            disabled={!canSend}
            className={`mb-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg transition ${
              canSend
                ? 'bg-emerald-600 hover:bg-emerald-500 active:scale-95'
                : 'cursor-not-allowed bg-gray-200'
            }`}
          >
            <SendIcon active={canSend} />
          </button>
        </div>
        <p className="mt-2 text-center text-xs text-gray-400">
          Hệ thống có thể mắc lỗi. Vui lòng kiểm chứng các dữ liệu quan trọng.
        </p>
      </div>
    </div>
  );
}

function SendIcon({ active }: { active: boolean }) {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
      <path
        d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"
        stroke={active ? 'white' : '#9ca3af'}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
