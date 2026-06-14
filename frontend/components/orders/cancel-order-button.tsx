"use client";

import { useState } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { cancelOrder } from "@/lib/api";
import { useReferenceDateStore } from "@/lib/store";

interface CancelOrderButtonProps {
  orderNo: string;
  onCancelled: () => void;
}

/** 4-3 표의 "취소" 버튼 — 확인 다이얼로그를 거쳐 E-6 주문 취소 API를 호출한다. */
export function CancelOrderButton({ orderNo, onCancelled }: CancelOrderButtonProps) {
  const referenceDate = useReferenceDateStore((s) => s.referenceDate);
  const [open, setOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleConfirm() {
    setIsSubmitting(true);
    setError(null);
    try {
      await cancelOrder(orderNo, referenceDate);
      setOpen(false);
      onCancelled();
    } catch (e) {
      setError(e instanceof Error ? e.message : "취소 중 오류가 발생했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="border-red-300 text-red-600 hover:bg-red-50 hover:text-red-700 hover:border-red-400"
        >
          취소
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>주문을 취소하시겠습니까?</AlertDialogTitle>
          <AlertDialogDescription>
            주문번호 {orderNo}을(를) 취소합니다. 이 작업은 되돌릴 수 없습니다.
            {error && <span className="mt-2 block text-destructive">{error}</span>}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isSubmitting}>닫기</AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault();
              void handleConfirm();
            }}
            disabled={isSubmitting}
          >
            {isSubmitting ? "취소 중..." : "주문 취소"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
