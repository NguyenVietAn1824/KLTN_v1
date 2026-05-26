import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Hệ thống hỏi đáp về chất lượng không khí',
  description: 'Trợ lý AI hỏi đáp dữ liệu chất lượng không khí',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="bg-white text-gray-900 antialiased">{children}</body>
    </html>
  );
}
