"use client";

import { useEffect } from "react";

import { DatePicker } from "@/components/ui/date-picker";
import { Label } from "@/components/ui/label";
import { useDashboard } from "@/lib/api";
import { useReferenceDateStore } from "@/lib/store";

/**
 * 전역 기준일(reference_date) 선택 컨트롤.
 *
 * - 최초 진입 시 store가 비어 있으면(null) 대시보드 API가 알려주는 기본값
 *   (SimulationConfig.start_date)으로 채운다.
 * - 사용자가 날짜를 바꾸면 전역 store를 갱신하고, 이를 구독하는 모든
 *   페이지/위젯의 SWR 쿼리가 자동으로 다시 호출된다.
 */
export function ReferenceDatePicker() {
  const referenceDate = useReferenceDateStore((s) => s.referenceDate);
  const setReferenceDate = useReferenceDateStore((s) => s.setReferenceDate);

  const { data } = useDashboard(referenceDate);

  useEffect(() => {
    if (referenceDate === null && data?.reference_date) {
      setReferenceDate(data.reference_date);
    }
  }, [referenceDate, data, setReferenceDate]);

  return (
    <div className="flex items-center gap-2">
      <Label htmlFor="reference-date" className="whitespace-nowrap text-sm text-white">
        기준일
      </Label>
      <DatePicker
        value={referenceDate}
        onChange={setReferenceDate}
        align="end"
        variant="header"
      />
    </div>
  );
}
