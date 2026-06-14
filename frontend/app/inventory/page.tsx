"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Clock, Factory, PackageX } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { ProductLedger } from "@/components/inventory/product-ledger";
import { ProductTable } from "@/components/inventory/product-table";
import { useDashboard, useProducts } from "@/lib/api";
import { useReferenceDateStore } from "@/lib/store";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  accent: "amber" | "red" | "navy";
}

const ACCENT_CLASSES: Record<MetricCardProps["accent"], { border: string; iconBg: string; iconColor: string }> = {
  amber: { border: "border-l-amber-400", iconBg: "bg-amber-50", iconColor: "text-amber-500" },
  red: { border: "border-l-red-500", iconBg: "bg-red-50", iconColor: "text-red-500" },
  navy: { border: "border-l-blue-800", iconBg: "bg-blue-50", iconColor: "text-blue-800" },
};

function MetricCard({ label, value, icon: Icon, accent }: MetricCardProps) {
  const classes = ACCENT_CLASSES[accent];
  return (
    <div className={cn("flex items-center gap-4 rounded-xl border border-hairline border-l-4 bg-white p-5 shadow-sm", classes.border)}>
      <div className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-full", classes.iconBg)}>
        <Icon className={cn("h-5 w-5", classes.iconColor)} />
      </div>
      <div>
        <p className="text-sm text-subtle mb-1">{label}</p>
        <p className="text-3xl font-bold tabular-nums text-ink">{value}</p>
      </div>
    </div>
  );
}

export default function InventoryPage() {
  const referenceDate = useReferenceDateStore((s) => s.referenceDate);
  const { data: dashboard } = useDashboard(referenceDate);
  const { data: products, isLoading, error } = useProducts(referenceDate);
  const [selectedSku, setSelectedSku] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedSku && products && products.length > 0) {
      setSelectedSku(products[0]!.sku);
    }
  }, [products, selectedSku]);

  const selectedProduct = products?.find((p) => p.sku === selectedSku) ?? null;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-ink">재고 현황</h1>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <MetricCard
          label="재주문점 이하 제품"
          value={dashboard?.products_below_reorder ?? "-"}
          icon={AlertTriangle}
          accent="amber"
        />
        <MetricCard
          label="재고 부족 제품"
          value={dashboard?.products_in_shortage ?? "-"}
          icon={PackageX}
          accent="red"
        />
        <MetricCard
          label="진행 중 생산발주"
          value={dashboard?.active_production_orders ?? "-"}
          icon={Factory}
          accent="navy"
        />
        <MetricCard
          label="지연 중인 주문"
          value={dashboard?.delayed_orders ?? "-"}
          icon={Clock}
          accent="red"
        />
      </div>

      {isLoading && <p className="text-sm text-subtle">제품 목록 불러오는 중...</p>}
      {error && (
        <div className="rounded-lg bg-red-100 border border-red-200 px-4 py-3 text-sm text-red-800">
          제품 목록을 불러오지 못했습니다.
        </div>
      )}

      {products && (
        <ProductTable products={products} selectedSku={selectedSku} onSelect={setSelectedSku} />
      )}

      {selectedProduct && (
        <div className="rounded-xl border border-hairline bg-white p-5 shadow-sm">
          <ProductLedger product={selectedProduct} />
        </div>
      )}
    </div>
  );
}
