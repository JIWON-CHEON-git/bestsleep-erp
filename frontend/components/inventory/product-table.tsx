"use client";

import { useMemo, useState } from "react";

import { ProductStatusBadge } from "@/components/status-badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { ProductRow, ProductStatus } from "@/lib/types";

const STATUS_FILTER_OPTIONS: { value: "all" | ProductStatus; label: string }[] = [
  { value: "all", label: "전체 상태" },
  { value: "shortage", label: "품절" },
  { value: "below_reorder", label: "발주됨" },
  { value: "warning", label: "주의" },
  { value: "normal", label: "정상" },
];

type SortKey = "current_stock" | "available_stock";

interface ProductTableProps {
  products: ProductRow[];
  selectedSku: string | null;
  onSelect: (sku: string) => void;
}

export function ProductTable({ products, selectedSku, onSelect }: ProductTableProps) {
  const [statusFilter, setStatusFilter] = useState<"all" | ProductStatus>("all");
  const [sort, setSort] = useState<{ key: SortKey; asc: boolean } | null>(null);

  const filtered = useMemo(() => {
    const base = statusFilter === "all" ? products : products.filter((p) => p.status === statusFilter);
    if (!sort) return base;
    return [...base].sort((a, b) => {
      const cmp = a[sort.key] - b[sort.key];
      return sort.asc ? cmp : -cmp;
    });
  }, [products, statusFilter, sort]);

  const toggleSort = (key: SortKey) => {
    setSort((prev) =>
      prev?.key === key ? { key, asc: !prev.asc } : { key, asc: true }
    );
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-ink">제품 목록</h2>
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as typeof statusFilter)}>
          <SelectTrigger className="w-[140px] h-8 text-sm">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUS_FILTER_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="overflow-hidden rounded-xl border border-hairline shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-table-head border-b border-hairline">
              <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">SKU</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">제품명</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">카테고리</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">
                <button
                  type="button"
                  className="flex items-center gap-1 hover:text-ink transition-colors ml-auto"
                  onClick={() => toggleSort("current_stock")}
                >
                  현재고 {sort?.key === "current_stock" ? (sort.asc ? "▲" : "▼") : ""}
                </button>
              </th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">
                <button
                  type="button"
                  className="flex items-center gap-1 hover:text-ink transition-colors ml-auto"
                  onClick={() => toggleSort("available_stock")}
                >
                  가용재고 {sort?.key === "available_stock" ? (sort.asc ? "▲" : "▼") : ""}
                </button>
              </th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">안전재고</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">재주문점</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">입고예정</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">백오더</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">상태</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p, idx) => (
              <tr
                key={p.sku}
                onClick={() => onSelect(p.sku)}
                className={cn(
                  "cursor-pointer transition-colors border-b border-gray-200 border-l-4",
                  p.sku === selectedSku
                    ? "bg-blue-50"
                    : idx % 2 === 1
                    ? "bg-gray-50/30 hover:bg-row-hover"
                    : "bg-white hover:bg-row-hover",
                  p.status === "shortage"
                    ? "border-l-red-500"
                    : p.status === "below_reorder" || p.status === "warning"
                    ? "border-l-amber-400"
                    : "border-l-transparent"
                )}
              >
                <td className="px-6 py-3 font-medium text-gray-900 tracking-wide">{p.sku}</td>
                <td className="px-6 py-3 font-medium text-gray-900">{p.name}</td>
                <td className="px-6 py-3 text-gray-600">{p.category} / {p.size}</td>
                <td className="px-6 py-3 text-right font-medium tabular-nums text-gray-900">{p.current_stock}</td>
                <td className={cn(
                  "px-6 py-3 text-right font-medium tabular-nums",
                  p.available_stock < 0 ? "text-red-800" : "text-gray-900"
                )}>
                  {p.available_stock}
                </td>
                <td className="px-6 py-3 text-right font-medium tabular-nums text-gray-500">{p.safety_stock}</td>
                <td className="px-6 py-3 text-right font-medium tabular-nums text-gray-500">{p.reorder_point}</td>
                <td className="px-6 py-3 text-right font-medium tabular-nums text-gray-700">{p.incoming_quantity}</td>
                <td className={cn(
                  "px-6 py-3 text-right font-medium tabular-nums",
                  p.backorder_count > 0 ? "text-orange-800" : "text-gray-400"
                )}>
                  {p.backorder_count > 0 ? p.backorder_count : "-"}
                </td>
                <td className="px-6 py-3">
                  <ProductStatusBadge status={p.status} />
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={10} className="px-6 py-8 text-center text-sm text-gray-500">
                  조건에 맞는 제품이 없습니다.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
