"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useProductLedger } from "@/lib/api";
import { useReferenceDateStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import type { ProductRow } from "@/lib/types";

interface ProductLedgerProps {
  product: ProductRow;
}

export function ProductLedger({ product }: ProductLedgerProps) {
  const referenceDate = useReferenceDateStore((s) => s.referenceDate);
  const { data: ledger, isLoading, error } = useProductLedger(
    product.sku,
    undefined,
    referenceDate ?? undefined
  );

  return (
    <div className="space-y-3">
      <h2 className="text-base font-semibold text-ink">
        제품별 재고 흐름 —{" "}
        <span className="text-subtle font-normal">{product.name} ({product.sku})</span>
        {" "}/ 일자별 원장
      </h2>

      {isLoading && <p className="text-sm text-subtle">불러오는 중...</p>}
      {error && <p className="text-sm text-red-800">원장을 불러오지 못했습니다.</p>}

      {ledger && ledger.length > 0 && (
        <>
          <div className="h-[200px] rounded-xl border border-hairline bg-white p-4 shadow-sm">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={ledger} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: "#6B7280" }}
                  interval="preserveStartEnd"
                  minTickGap={24}
                />
                <YAxis tick={{ fontSize: 11, fill: "#6B7280" }} />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #E2E8F0", background: "#fff", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}
                  labelFormatter={(label) => `날짜: ${label}`}
                  formatter={(value, name) => [value, name]}
                />
                <Legend verticalAlign="top" align="right" height={32} wrapperStyle={{ fontSize: 12 }} />
                <Line
                  type="monotone"
                  dataKey="closing_stock"
                  name="기말재고"
                  stroke="#2B4270"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="available_stock"
                  name="가용재고"
                  stroke="#10B981"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="overflow-hidden rounded-xl border border-hairline shadow-sm">
            <div className="max-h-[420px] overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 z-10">
                  <tr className="bg-table-head border-b border-hairline">
                    <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">일자</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">기초재고</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">생산입고(+)</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">주문출고(-)</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">기말재고</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">가용재고</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">생산발주</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-table-head-foreground uppercase tracking-wider">백오더</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-table-head-foreground uppercase tracking-wider">이벤트</th>
                  </tr>
                </thead>
                <tbody>
                  {ledger.map((row, idx) => (
                    <tr
                      key={row.date}
                      className={cn(
                        "transition-colors border-b border-gray-200 border-l-4",
                        row.structural_shortage_flag
                          ? "border-l-red-500"
                          : row.order_quantity_today > 0
                          ? "border-l-blue-800"
                          : row.available_stock < 0
                          ? "border-l-red-500"
                          : row.backorder_balance > 0
                          ? "border-l-amber-400"
                          : "border-l-transparent",
                        row.structural_shortage_flag
                          ? "bg-[#FFF5F5]"
                          : row.order_quantity_today > 0
                          ? "bg-[#EFF6FF]"
                          : row.backorder_balance > 0
                          ? "bg-orange-50"
                          : idx % 2 === 1
                          ? "bg-gray-50/30 hover:bg-row-hover"
                          : "bg-white hover:bg-row-hover"
                      )}
                    >
                      <td className="px-6 py-3 font-medium text-gray-900 tracking-wide">{row.date}</td>
                      <td className="px-6 py-3 text-right font-medium tabular-nums text-gray-600">{row.opening_stock}</td>
                      <td className="px-6 py-3 text-right tabular-nums font-medium text-emerald-600">
                        {row.production_inbound > 0 ? `+${row.production_inbound}` : <span className="text-gray-300">—</span>}
                      </td>
                      <td className="px-6 py-3 text-right tabular-nums font-medium text-red-600">
                        {row.order_outbound > 0 ? `-${row.order_outbound}` : <span className="text-gray-300">—</span>}
                      </td>
                      <td className="px-6 py-3 text-right tabular-nums font-semibold text-gray-900">{row.closing_stock}</td>
                      <td className={cn(
                        "px-6 py-3 text-right tabular-nums font-semibold",
                        row.available_stock < 0 ? "text-red-800" : "text-gray-900"
                      )}>
                        {row.available_stock}
                      </td>
                      <td className="px-6 py-3 text-right tabular-nums text-blue-800 font-medium">
                        {row.order_quantity_today > 0 ? row.order_quantity_today : <span className="text-gray-300">—</span>}
                      </td>
                      <td className={cn(
                        "px-6 py-3 text-right tabular-nums font-medium",
                        row.backorder_balance > 0 ? "text-orange-800" : "text-gray-300"
                      )}>
                        {row.backorder_balance > 0 ? row.backorder_balance : "—"}
                      </td>
                      <td className="px-6 py-3 text-sm text-blue-800 max-w-[200px]">{row.events}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {ledger && ledger.length === 0 && (
        <p className="text-sm text-subtle">원장 데이터가 없습니다.</p>
      )}
    </div>
  );
}
