import { create } from "zustand";

/**
 * 기준일(reference_date) 전역 상태.
 *
 * 모든 페이지/위젯이 같은 기준일을 바라봐야 하므로 (E-1~E-5 API 모두
 * reference_date 쿼리 파라미터를 받음) 전역으로 둔다. 초기값은 백엔드의
 * SimulationConfig.start_date를 모르는 시점이라 null로 시작하고,
 * 최초 데이터 로드 시(예: 대시보드) 받아온 값으로 채운다.
 */
interface ReferenceDateState {
  referenceDate: string | null;
  setReferenceDate: (date: string) => void;
}

export const useReferenceDateStore = create<ReferenceDateState>((set) => ({
  referenceDate: null,
  setReferenceDate: (date) => set({ referenceDate: date }),
}));
