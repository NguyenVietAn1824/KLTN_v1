'use client';

import type { Conversation } from '@/types';

interface Props {
  open: boolean;
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  userId: string;
  onLogout?: () => void;
}

export default function Sidebar({
  open,
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  userId,
  onLogout,
}: Props) {
  return (
    <aside
      aria-hidden={!open}
      className={`flex h-full flex-shrink-0 flex-col overflow-hidden bg-gray-50 transition-[width,border-color] duration-300 ease-in-out ${
        open ? 'w-[280px] border-r border-gray-200' : 'w-0 border-r border-transparent'
      }`}
    >
      <div
        className={`flex h-full w-[280px] flex-col transition-opacity duration-200 ${
          open ? 'opacity-100 delay-100' : 'pointer-events-none opacity-0'
        }`}
      >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-3">
        <div className="flex items-center gap-2 px-2">
          <AirIcon />
          <span className="text-sm font-semibold text-gray-900">Chất lượng không khí</span>
        </div>
        <button
          onClick={onNewChat}
          title="Cuộc trò chuyện mới"
          className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-500 transition hover:bg-gray-200 hover:text-gray-900"
        >
          <PencilIcon />
        </button>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {conversations.length === 0 ? (
          <p className="px-3 py-3 text-xs text-gray-400">Chưa có cuộc trò chuyện nào</p>
        ) : (
          <>
            <p className="px-3 py-1.5 text-xs font-medium text-gray-500">Gần đây</p>
            <div className="space-y-0.5">
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={`group flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition ${
                    conv.id === activeConversationId
                      ? 'bg-emerald-50 text-emerald-900'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <ChatBubbleIcon className="flex-shrink-0 text-gray-400" />
                  <span className="flex-1 truncate">{conv.title}</span>
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Footer - user */}
      <div className="border-t border-gray-200 px-3 py-3">
        <div className="flex items-center gap-2 rounded-lg px-2 py-1.5">
          <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-emerald-600 text-xs font-bold text-white">
            {userId.charAt(0).toUpperCase()}
          </div>
          <span className="flex-1 truncate text-sm text-gray-700">{userId}</span>
          {onLogout && (
            <button
              type="button"
              onClick={onLogout}
              title="Đăng xuất"
              className="flex h-7 w-7 items-center justify-center rounded-lg text-gray-500 transition hover:bg-gray-200 hover:text-gray-900"
            >
              <LogoutIcon />
            </button>
          )}
        </div>
      </div>
      </div>
    </aside>
  );
}

function AirIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path
        d="M9.59 4.59A2 2 0 1111 8H2m10.59 11.41A2 2 0 1014 16H2m15.73-8.27A2.5 2.5 0 1119.5 12H2"
        stroke="#059669"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function PencilIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

function ChatBubbleIcon({ className }: { className?: string }) {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
  );
}
