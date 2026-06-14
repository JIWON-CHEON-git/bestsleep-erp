"use client";

import { useMemo, useState } from "react";

import { CancelOrderButton } from "@/components/orders/cancel-order-button";
import { OrderStatusBadge } from "@/components/status-badge";
import { DatePicker } from "@/components/ui/date-picker";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useOrders, useProducts } from "@/lib/api";
import { useReferenceDateStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import type { OrderViewStatus } from "@/lib/types";

const STATUS_FILTER_OPTIONS: { value: "all" | OrderViewStatus; label: string }[] = [
  { value: "all", label: "전체 상태" },
  { value: "pending", label: "배송 대기" },
  { value: "normal", label: "정상 배송" },
  { value: "simple_delay", label: "배송 지연" },
  { value: "promise_kept", label: "기한 내 배송" },
  { value: "promise_broken", label: "기한 초과" },
  { value: "cancelled", label: "주문 취소" },
];

export default function OrdersPage() {
  const referenceDate = useReferenceDateStore((s) => s.referenceDate);
  const [statusFilter, setStatusFilter] = useState<"all" | OrderViewStatus>("all");
  const [skuFilter, setSkuFilter] = useState<string>("all");
  const [orderDateFilter, setOrderDateFilter] = useState<string>("");

  const { data: products } = useProducts(referenceDate);
  const { data, isLoading, error, mutate } = useOrders({
    referenceDate,
    status: statusFilter === "all" ? undefined : statusFilter,
    sku: skuFilter === "all" ? undefined : skuFilter,
  });

  const filtered = useMemo(() => {
    if (!data) return data;
    if (!orderDateFilter) return data;
    return data.filter((o) => o.order_date === orderDateFilter);
  }, [data, orderDateFilter]);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-ink">배송 안내</h1>

      <div className="flex flex-wrap items-end gap-3">
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as typeof statusFilter)}>
          <SelectTrigger className="w-[160px] h-9 text-sm">
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
          <label className="text-xs text-gray-500">주문일</label>
          <DatePicker
            value={orderDateFilter || null}
            onChange={setOrderDateFilter}
            onClear={() => setOrderDateFilter("")}
            placeholder="전체 기간"
          />
        </div>
      </div>

      {isLoading && <p className="text-sm text-gray-500">불러오는 중...</p>}
      {error && (
        <div className="rounded-lg bg-red-100 border border-red-200 px-4 py-3 text-sm text-red-800">
          주문 목록을 불러오지 못했습니다.
        </div>
      )}

      {filtered && (
        <div className="overflow-hidden rounded-xl border border-hairline shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-table-head border-b border-hairline">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider whitespace-nowrap">주문번호</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider whitespace-nowrap">주문일</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">제품</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">수량</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">고객명</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider whitespace-nowrap">희망배송일</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider whitespace-nowrap">출고일</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider whitespace-nowrap">도착예정일</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">상태</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">비고</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-table-head-foreground uppercase tracking-wider">취소</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((o, idx) => (
                  <tr
                    key={o.order_no}
                    className={cn(
                      "transition-colors border-b border-gray-200 border-l-4",
                      o.status === "promise_broken" || o.status === "simple_delay"
                        ? "border-l-red-500"
                        : "border-l-transparent",
                      o.status === "promise_broken"
                        ? "bg-red-50 hover:bg-red-100"
                        : o.status === "simple_delay"
                        ? "bg-orange-50 hover:bg-orange-100"
                        : o.status === "pending"
                        ? "bg-gray-50 hover:bg-gray-100"
                        : o.status === "cancelled"
                        ? "bg-gray-50 opacity-60"
                        : idx % 2 === 1
                        ? "bg-gray-50/30 hover:bg-row-hover"
                        : "bg-white hover:bg-row-hover"
                    )}
                  >
                    <td className="px-6 py-3 font-medium text-gray-900 tracking-wide">{o.order_no}</td>
                    <td className="px-6 py-3 font-medium text-gray-900 tracking-wide">{o.order_date}</td>
                    <td className="px-6 py-3">
                      <div className="font-medium text-gray-900">{o.product_name}</div>
                      <div className="text-xs text-gray-500 font-medium tracking-wide">{o.sku}</div>
                    </td>
                    <td className="px-6 py-3 text-right font-medium tabular-nums text-gray-900">{o.quantity}</td>
                    <td className="px-6 py-3 text-gray-700">{o.customer_name}</td>
                    <td className="px-6 py-3 font-medium text-gray-900 tracking-wide">{o.desired_delivery_date ?? "—"}</td>
                    <td className="px-6 py-3 font-medium text-gray-900 tracking-wide">{o.shipped_date ?? "—"}</td>
                    <td className="px-6 py-3 font-medium text-gray-900 tracking-wide">{o.expected_arrival_date ?? "—"}</td>
                    <td className="px-6 py-3">
                      <div className="flex flex-col gap-1 items-start">
                        <OrderStatusBadge status={o.status} />
                        {o.status !== "pending" && o.status !== "cancelled" && (
                          <span
                            className={cn(
                              "text-xs",
                              o.expected_arrival_date && referenceDate && o.expected_arrival_date <= referenceDate
                                ? "text-emerald-600 font-medium"
                                : "text-gray-500"
                            )}
                          >
                            {o.expected_arrival_date && referenceDate && o.expected_arrival_date <= referenceDate
                              ? "배송 완료"
                              : "배송 중"}
                          </span>
                        )}
                        {o.delay_days > 0 && (
                          <span className="text-xs text-orange-700">{o.delay_days}일 지연</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-3 text-sm text-gray-600 max-w-[240px]">{o.root_cause || "—"}</td>
                    <td className="px-6 py-3 text-center">
                      {o.is_cancellable ? (
                        <CancelOrderButton orderNo={o.order_no} onCancelled={() => mutate()} />
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={11} className="px-6 py-8 text-center text-sm text-gray-500">
                      조건에 맞는 주문이 없습니다.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
