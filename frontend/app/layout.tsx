import type { Metadata } from "next";
import { Inter, Noto_Sans_KR, Noto_Serif_KR } from "next/font/google";

import { Nav } from "@/components/nav";
import { ReferenceDatePicker } from "@/components/reference-date-picker";

import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const notoSansKr = Noto_Sans_KR({
  subsets: ["latin"],
  weight: ["400", "500", "700", "900"],
  variable: "--font-noto-sans-kr",
});
const notoSerifKr = Noto_Serif_KR({
  subsets: ["latin"],
  weight: ["700", "900"],
  variable: "--font-noto-serif-kr",
});

export const metadata: Metadata = {
  title: "베스트슬립 재고흐름 ERP",
  description: "주문 → 재고 → 발주(생산) → 입고 → 배송 흐름 추적",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body
        className={`${inter.variable} ${notoSansKr.variable} ${notoSerifKr.variable} bg-surface text-ink antialiased font-sans`}
      >
        <header className="sticky top-0 z-50 bg-brand-navy">
          <div className="w-full px-6 flex h-16 items-stretch justify-between">
            <div className="flex items-stretch gap-6">
              <span className="flex items-center font-serif text-xl font-bold tracking-tight text-white">
                베스트슬립 ERP
              </span>
              <Nav />
            </div>
            <div className="flex items-center">
              <ReferenceDatePicker />
            </div>
          </div>
        </header>
        <main className="w-full px-8 py-8">{children}</main>
      </body>
    </html>
  );
}
