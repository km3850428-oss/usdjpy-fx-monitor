import type { Metadata } from "next";
import { Geist_Mono } from "next/font/google";
import "./globals.css";

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "USD/JPY ライブダッシュボード",
  description: "ドル円のテクニカル・ファンダメンタルズ判定と仮想トレード成績をライブ表示",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" className={geistMono.variable}>
      <body>{children}</body>
    </html>
  );
}
