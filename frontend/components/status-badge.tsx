import { cn } from "@/lib/utils";
import type { OrderViewStatus, ProductionOrderDisplayStatus, ProductStatus } from "@/lib/types";

const PRODUCT_STATUS_LABELS: Record<ProductStatus, string> = {
  normal: "정상",
  warning: "주의",
  below_reorder: "발주됨",
  shortage: "부족",
};

const PRODUCT_STATUS_CLASSES: Record<ProductStatus, string> = {
  normal: "bg-[#F1F5F9] text-[#475569]",
  warning: "bg-[#FEF3C7] text-[#92400E]",
  below_reorder: "bg-[#DBEAFE] text-[#1E40AF]",
  shortage: "bg-[#FEE2E2] text-[#991B1B]",
};

export function ProductStatusBadge({ status }: { status: ProductStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        PRODUCT_STATUS_CLASSES[status]
      )}
    >
      {PRODUCT_STATUS_LABELS[status]}
    </span>
  );
}

const PRODUCTION_ORDER_STATUS_LABELS: Record<ProductionOrderDisplayStatus, string> = {
  pending: "입고 예정",
  received: "입고 완료",
};

const PRODUCTION_ORDER_STATUS_CLASSES: Record<ProductionOrderDisplayStatus, string> = {
  pending: "bg-[#DBEAFE] text-[#1E40AF]",
  received: "bg-[#DCFCE7] text-[#166534]",
};

export function ProductionOrderStatusBadge({ status }: { status: ProductionOrderDisplayStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        PRODUCTION_ORDER_STATUS_CLASSES[status]
      )}
    >
      {PRODUCTION_ORDER_STATUS_LABELS[status]}
    </span>
  );
}

const ORDER_STATUS_LABELS: Record<OrderViewStatus, string> = {
  pending: "배송 대기",
  normal: "정상 배송",
  simple_delay: "배송 지연",
  promise_kept: "기한 내 배송",
  promise_broken: "기한 초과",
  cancelled: "주문 취소",
};

const ORDER_STATUS_CLASSES: Record<OrderViewStatus, string> = {
  pending: "bg-[#FED7AA] text-[#9A3412]",
  normal: "bg-[#F1F5F9] text-[#475569]",
  simple_delay: "bg-[#FEF3C7] text-[#92400E]",
  promise_kept: "bg-[#DCFCE7] text-[#166534]",
  promise_broken: "bg-[#FEE2E2] text-[#991B1B]",
  cancelled: "bg-[#F1F5F9] text-[#9CA3AF] line-through",
};

export function OrderStatusBadge({ status }: { status: OrderViewStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        ORDER_STATUS_CLASSES[status]
      )}
    >
      {ORDER_STATUS_LABELS[status]}
    </span>
  );
}
