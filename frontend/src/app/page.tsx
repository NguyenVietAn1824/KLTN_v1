'use client';

import { useState, useCallback, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import Sidebar from '@/components/Sidebar';
import ChatWindow from '@/components/ChatWindow';
import AuthScreen from '@/components/AuthScreen';
import type { Conversation, Message } from '@/types';

const AQI_API = '/proxy/v1/aqi_agent';
const STORAGE_KEY = 'aqi_user_email';

interface ConvSummary {
  id: string;
  title: string;
  created_at: string | null;
}

interface MessageRow {
  id: string;
  question: string;
  answer: string;
  created_at: string | null;
}

export default function Home() {
  const [userId, setUserId] = useState('');
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [bootstrapping, setBootstrapping] = useState(true);

  const activeConversation = conversations.find((c) => c.id === activeConversationId) ?? null;

  useEffect(() => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;
    if (saved) setUserId(saved);
    setBootstrapping(false);
  }, []);

  const loadConversationMessages = useCallback(
    async (email: string, convId: string): Promise<Message[]> => {
      const res = await fetch(
        `/proxy/v1/conversations/${convId}/messages?email=${encodeURIComponent(email)}`,
      );
      if (!res.ok) return [];
      const data: { info: { messages: MessageRow[] } } = await res.json();
      const out: Message[] = [];
      for (const row of data.info.messages || []) {
        const ts = row.created_at ? new Date(row.created_at) : new Date();
        out.push({ id: `${row.id}-q`, role: 'user', content: row.question, timestamp: ts });
        if (row.answer) {
          out.push({ id: `${row.id}-a`, role: 'assistant', content: row.answer, timestamp: ts });
        }
      }
      return out;
    },
    [],
  );

  useEffect(() => {
    if (!userId) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/proxy/v1/conversations?email=${encodeURIComponent(userId)}`);
        if (!res.ok) return;
        const data: { info: { conversations: ConvSummary[] } } = await res.json();
        const summaries = data.info.conversations || [];

        const loaded: Conversation[] = await Promise.all(
          summaries.map(async (c) => ({
            id: c.id,
            title: c.title || 'Untitled',
            createdAt: c.created_at ? new Date(c.created_at) : new Date(),
            messages: await loadConversationMessages(userId, c.id),
          })),
        );
        if (!cancelled) setConversations(loaded);
      } catch {
        // ignore — user can still start a new chat
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId, loadConversationMessages]);

  const handleAuthenticated = useCallback((email: string) => {
    localStorage.setItem(STORAGE_KEY, email);
    setUserId(email);
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setUserId('');
    setConversations([]);
    setActiveConversationId(null);
  }, []);

  const handleNewChat = useCallback(() => {
    setActiveConversationId(null);
  }, []);

  const sendMessage = useCallback(
    async (question: string) => {
      if (!question.trim() || isLoading) return;

      let convId = activeConversationId;

      if (!convId) {
        convId = uuidv4();
        const title = question.length > 48 ? question.slice(0, 48) + '…' : question;
        setConversations((prev) => [
          { id: convId!, title, messages: [], createdAt: new Date() },
          ...prev,
        ]);
        setActiveConversationId(convId);
      }

      const userMsg: Message = {
        id: uuidv4(),
        role: 'user',
        content: question,
        timestamp: new Date(),
      };
      const loadingMsg: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isLoading: true,
      };

      setConversations((prev) =>
        prev.map((c) =>
          c.id === convId
            ? { ...c, messages: [...c.messages, userMsg, loadingMsg] }
            : c,
        ),
      );
      setIsLoading(true);

      try {
        const res = await fetch(AQI_API, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question,
            conversation_id: convId,
            user_id: userId,
          }),
        });

        if (!res.ok) {
          const text = await res.text().catch(() => '');
          throw new Error(text || `HTTP ${res.status}`);
        }

        const data: { info: { response: string } } = await res.json();

        setConversations((prev) =>
          prev.map((c) =>
            c.id === convId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.isLoading
                      ? { ...m, content: data.info.response, isLoading: false }
                      : m,
                  ),
                }
              : c,
          ),
        );
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : 'An unexpected error occurred.';
        setConversations((prev) =>
          prev.map((c) =>
            c.id === convId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.isLoading
                      ? {
                          ...m,
                          content: `**Could not reach the AQI Agent service.**\n\n${msg}\n\nMake sure the service is running on port 3334.`,
                          isLoading: false,
                          isError: true,
                        }
                      : m,
                  ),
                }
              : c,
          ),
        );
      } finally {
        setIsLoading(false);
      }
    },
    [activeConversationId, isLoading, userId],
  );

  if (bootstrapping) return null;
  if (!userId) return <AuthScreen onAuthenticated={handleAuthenticated} />;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        open={sidebarOpen}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={setActiveConversationId}
        onNewChat={handleNewChat}
        userId={userId}
        onLogout={handleLogout}
      />
      <ChatWindow
        conversation={activeConversation}
        isLoading={isLoading}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((o) => !o)}
        onSendMessage={sendMessage}
        onSuggestionClick={sendMessage}
      />
    </div>
  );
}
