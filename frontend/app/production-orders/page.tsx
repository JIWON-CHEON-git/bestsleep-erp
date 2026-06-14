"use client";

import { useMemo, useState } from "react";

import { ProductionOrderStatusBadge } from "@/components/status-badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useProducts, useProductionOrders } from "@/lib/api";
import { useReferenceDateStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import type { ProductionOrderDisplayStatus } from "@/lib/types";

const STATUS_FILTER_OPTIONS: { value: "all" | ProductionOrderDisplayStatus; label: string }[] = [
  { value: "all", label: "전체 상태" },
  { value: "pending", label: "입고 예정" },
  { value: "received", label: "입고 완료" },
];

export default function ProductionOrdersPage() {
  const referenceDate = useReferenceDateStore((s) => s.referenceDate);
  const [statusFilter, setStatusFilter] = useState<"all" | ProductionOrderDisplayStatus>("all");
  const [skuFilter, setSkuFilter] = useState<string>("all");
  const [orderDateFilter, setOrderDateFilter] = useState<string>("");
  const [sortAsc, setSortAsc] = useState(true);

  const { data: products } = useProducts(referenceDate);
  const { data, isLoading, error } = useProductionOrders({
    referenceDate,
    status: statusFilter === "all" ? undefined : statusFilter,
    sku: skuFilter === "all" ? undefined : skuFilter,
  });

  const sorted = useMemo(() => {
    if (!data) return data;
    const filtered = orderDateFilter
      ? data.filter((po) => po.order_date === orderDateFilter)
      : data;
    return [...filtered].sort((a, b) => {
      const cmp = a.expected_arrival_date.localeCompare(b.expected_arrival_date);
      return sortAsc ? cmp : -cmp;
    });
  }, [data, orderDateFilter, sortAsc]);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-ink">생산발주 목록</h1>

      <div className="flex flex-wrap items-center gap-3">
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as typeof statusFilter)}>
          <SelectTrigger className="w-[140px] h-9 text-sm">
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

        <Select value={skuFilter} onValueChange={setSkuFilter}>
          <SelectTrigger className="w-[200px] h-9 text-sm">
            <SelectValue placeholder="전체 제품" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">전체 제품</SelectItem>
            {products?.map((p) => (
              <SelectItem key={p.sku} value={p.sku}>
                {p.name} ({p.sku})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500">발주일</label>
          <Input
            type="date"
            value={orderDateFilter}
            onChange={(e) => setOrderDateFilter(e.target.value)}
            className="w-[150px] h-9 text-sm"
          />
        </div>
      </div>

      {isLoading && <p className="text-sm text-gray-500">불러오는 중...</p>}
      {error && (
        <div className="rounded-lg bg-red-100 border border-red-200 px-4 py-3 text-sm text-red-800">
          생산발주 목록을 불러오지 못했습니다.
        </div>
      )}

      {sorted && (
        <div className="overflow-hidden rounded-xl border border-hairline shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-table-head border-b border-hairline">
                <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">발주일</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">SKU</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">제품명</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">발주수량</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">
                  <button
                    type="button"
                    className="flex items-center gap-1 hover:text-ink transition-colors"
                    onClick={() => setSortAsc((v) => !v)}
                  >
                    입고예정일 {sortAsc ? "▲" : "▼"}
                  </button>
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">상태</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">발주 이유</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((po, idx) => (
                <tr
                  key={po.id}
                  className={cn(
                    "transition-colors border-b border-gray-200",
                    idx % 2 === 1 ? "bg-gray-50/30 hover:bg-row-hover" : "bg-white hover:bg-row-hover"
                  )}
                >
                  <td className="px-6 py-3 font-medium text-gray-900 tracking-wide">{po.order_date}</td>
                  <td className="px-6 py-3 font-medium text-gray-900 tracking-wide">{po.sku}</td>
                  <td className="px-6 py-3 font-medium text-gray-900">{po.product_name}</td>
                  <td className="px-6 py-3 text-right font-medium tabular-nums text-gray-900">{po.quantity}</td>
                  <td className="px-6 py-3 font-medium text-gray-900 tracking-wide">{po.expected_arrival_date}</td>
                  <td className="px-6 py-3">
                    <ProductionOrderStatusBadge status={po.status} />
                  </td>
                  <td className="px-6 py-3 text-sm text-gray-600">{po.trigger_reason}</td>
                </tr>
              ))}
              {sorted.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-sm text-gray-500">
                    조건에 맞는 생산발주가 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
