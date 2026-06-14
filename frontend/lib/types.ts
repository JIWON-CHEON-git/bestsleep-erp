/** 백엔드 REST API(E-1 ~ E-7) 응답 타입. */

export type ProductStatus = "normal" | "warning" | "below_reorder" | "shortage";

export type OrderViewStatus =
  | "pending"
  | "normal"
  | "simple_delay"
  | "promise_kept"
  | "promise_broken"
  | "cancelled";

export type ProductionOrderDisplayStatus = "pending" | "received";

/** E-1 GET /api/dashboard/ */
export interface DashboardResponse {
  reference_date: string;
  products_below_reorder: number;
  products_in_shortage: number;
  active_production_orders: number;
  delayed_orders: number;
  broken_promise_orders: number;
  structural_shortage_products: string[];
}

/** E-2 GET /api/products/ 의 한 행 */
export interface ProductRow {
  sku: string;
  name: string;
  category: string;
  size: string;
  safety_stock: number;
  reorder_point: number;
  current_stock: number;
  available_stock: number;
  incoming_quantity: number;
  backorder_count: number;
  status: ProductStatus;
}

/** E-3 GET /api/products/<sku>/ledger/ 의 한 행 */
export interface DailyLedgerRow {
  date: string;
  opening_stock: number;
  production_inbound: number;
  order_outbound: number;
  closing_stock: number;
  available_stock: number;
  order_quantity_today: number;
  backorder_balance: number;
  structural_shortage_flag: boolean;
  events: string;
}

/** E-4 GET /api/production-orders/ 의 한 행 */
export interface ProductionOrderRow {
  id: number;
  sku: string;
  product_name: string;
  order_date: string;
  quantity: number;
  expected_arrival_date: string;
  received_date: string | null;
  trigger_reason: string;
  status: ProductionOrderDisplayStatus;
}

/** E-5 GET /api/orders/ 의 한 행 */
export interface OrderRow {
  order_no: string;
  order_date: string;
  sku: string;
  product_name: string;
  quantity: number;
  customer_name: string;
  desired_delivery_date: string | null;
  status: OrderViewStatus;
  stock_deducted_date: string | null;
  shipped_date: string | null;
  expected_arrival_date: string | null;
  delay_days: number;
  root_cause: string;
  is_cancellable: boolean;
}

/** E-7 POST /api/simulation/run/ */
export interface SimulationRunResponse {
  products: number;
  ledger_rows: number;
  production_orders: number;
  orders: number;
}
