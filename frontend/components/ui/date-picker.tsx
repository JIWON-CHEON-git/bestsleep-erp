"use client"

import * as React from "react"
import { format, parseISO } from "date-fns"
import { CalendarIcon, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"

interface DatePickerProps {
  value?: string | null;
  onChange: (value: string) => void;
  onClear?: () => void;
  placeholder?: string;
  className?: string;
  align?: "start" | "center" | "end";
  variant?: "default" | "header";
}

export function DatePicker({
  value,
  onChange,
  onClear,
  placeholder = "날짜 선택",
  className,
  align = "start",
  variant = "default",
}: DatePickerProps) {
  const [open, setOpen] = React.useState(false);
  const selected = value ? parseISO(value) : undefined;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          className={cn(
            "h-9 w-[150px] justify-start gap-2 text-left text-sm font-normal",
            variant === "header"
              ? cn(
                  "border-white/30 bg-white/10 text-white hover:bg-white/20 hover:text-white",
                  !value && "text-white/70"
                )
              : !value && "text-gray-400",
            className
          )}
        >
          <CalendarIcon className={cn("h-4 w-4", variant === "header" ? "text-white/70" : "text-gray-400")} />
          {selected ? format(selected, "yyyy-MM-dd") : placeholder}
          {value && onClear && (
            <X
              className={cn(
                "ml-auto h-4 w-4",
                variant === "header" ? "text-white/70 hover:text-white" : "text-gray-400 hover:text-gray-700"
              )}
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                onClear();
              }}
            />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align={align} className="w-auto p-0">
        <Calendar
          mode="single"
          selected={selected}
          defaultMonth={selected}
          onSelect={(date) => {
            if (date) {
              onChange(format(date, "yyyy-MM-dd"));
              setOpen(false);
            }
          }}
        />
      </PopoverContent>
    </Popover>
  );
}
