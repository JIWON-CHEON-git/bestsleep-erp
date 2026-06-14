import useSWR from "swr";

import type {
  DashboardResponse,
  DailyLedgerRow,
  OrderRow,
  ProductionOrderRow,
  ProductRow,
  SimulationRunResponse,
} from "@/lib/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `요청 실패: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

/** referenceDate가 null이면 쿼리 파라미터를 생략한다 (백엔드가 시작일을 기본값으로 사용). */
function buildQuery(params: Record<string, string | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, value);
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

/** E-1 대시보드 */
export function useDashboard(referenceDate: string | null) {
  const query = buildQuery({ reference_date: referenceDate });
  return useSWR<DashboardResponse>(`${API_BASE_URL}/dashboard/${query}`, fetcher);
}

/** E-2 제품 목록 */
export function useProducts(referenceDate: string | null) {
  const query = buildQuery({ reference_date: referenceDate });
  return useSWR<ProductRow[]>(`${API_BASE_URL}/products/${query}`, fetcher);
}

/** E-3 제품별 일자별 원장 */
export function useProductLedger(sku: string | null, start?: string, end?: string) {
  const query = buildQuery({ start, end });
  return useSWR<DailyLedgerRow[]>(
    sku ? `${API_BASE_URL}/products/${sku}/ledger/${query}` : null,
    fetcher
  );
}

/** E-4 생산발주 목록 */
export function useProductionOrders(params: {
  referenceDate: string | null;
  status?: string;
  sku?: string;
}) {
  const query = buildQuery({
    reference_date: params.referenceDate,
    status: params.status,
    sku: params.sku,
  });
  return useSWR<ProductionOrderRow[]>(`${API_BASE_URL}/production-orders/${query}`, fetcher);
}

/** E-5 주문 목록 */
export function useOrders(params: {
  referenceDate: string | null;
  status?: string;
  sku?: string;
  customerName?: string;
}) {
  const query = buildQuery({
    reference_date: params.referenceDate,
    status: params.status,
    sku: params.sku,
    customer_name: params.customerName,
  });
  return useSWR<OrderRow[]>(`${API_BASE_URL}/orders/${query}`, fetcher);
}

/** E-6 주문 취소 */
export async function cancelOrder(orderNo: string, referenceDate: string | null): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/orders/${orderNo}/cancel/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reference_date: referenceDate }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `취소 실패: ${res.status}`);
  }
}

/** E-7 시뮬레이션 재실행 */
export async function runSimulation(): Promise<SimulationRunResponse> {
  const res = await fetch(`${API_BASE_URL}/simulation/run/`, { method: "POST" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `재실행 실패: ${res.status}`);
  }
  return res.json() as Promise<SimulationRunResponse>;
}
