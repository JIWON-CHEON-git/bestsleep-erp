"use client"

import * as React from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { DayPicker } from "react-day-picker"
import { ko } from "date-fns/locale"

import { cn } from "@/lib/utils"

export type CalendarProps = React.ComponentProps<typeof DayPicker>

function Calendar({ className, classNames, showOutsideDays = true, ...props }: CalendarProps) {
  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      locale={ko}
      className={cn("p-3", className)}
      classNames={{
        months: "flex flex-col",
        month: "space-y-2",
        month_caption: "relative flex items-center justify-center pt-1 pb-2",
        caption_label: "text-sm font-semibold text-gray-900",
        nav: "absolute inset-x-0 top-0 flex items-center justify-between",
        button_previous:
          "h-8 w-8 flex items-center justify-center rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-900 transition-colors disabled:opacity-30",
        button_next:
          "h-8 w-8 flex items-center justify-center rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-900 transition-colors disabled:opacity-30",
        month_grid: "w-full border-collapse",
        weekdays: "flex",
        weekday: "h-10 w-10 text-center text-sm font-medium text-gray-500",
        weeks: "",
        week: "flex w-full mt-1",
        day: "h-10 w-10 p-0 text-center text-sm relative",
        day_button:
          "h-10 w-10 rounded-md text-sm font-medium text-gray-900 hover:bg-blue-50 transition-colors flex items-center justify-center",
        selected: "[&>button]:bg-blue-600 [&>button]:text-white [&>button]:hover:bg-blue-600",
        today: "[&>button]:border [&>button]:border-blue-600 [&>button]:font-semibold",
        outside: "[&>button]:text-gray-300",
        disabled: "[&>button]:text-gray-300 [&>button]:opacity-50 [&>button]:hover:bg-transparent",
        hidden: "invisible",
        ...classNames,
      }}
      components={{
        Chevron: ({ orientation }) =>
          orientation === "left" ? (
            <ChevronLeft className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          ),
      }}
      {...props}
    />
  )
}
Calendar.displayName = "Calendar"

export { Calendar }
