"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/inventory", label: "재고 현황" },
  { href: "/production-orders", label: "생산발주" },
  { href: "/orders", label: "배송 안내" },
] as const;

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="flex items-stretch gap-1">
      {NAV_ITEMS.map((item) => {
        const active = pathname?.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center border-b-2 px-3 text-sm font-medium transition-colors",
              active
                ? "border-white bg-white/10 text-white"
                : "border-transparent text-white/70 hover:bg-white/10 hover:text-white"
            )}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
