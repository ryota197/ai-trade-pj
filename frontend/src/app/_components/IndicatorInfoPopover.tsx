"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { HelpCircle, ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { IndicatorId } from "@/lib/indicator-guide";
import { getIndicatorGuide } from "@/lib/indicator-guide";

interface IndicatorInfoPopoverProps {
  indicatorId: IndicatorId;
}

/**
 * 指標情報ポップオーバー
 *
 * ?アイコンをクリックすると指標の簡易説明を表示
 * 「詳しく見る」リンクでガイドページへ遷移
 */
export function IndicatorInfoPopover({ indicatorId }: IndicatorInfoPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const guide = getIndicatorGuide(indicatorId);

  // クリック外で閉じる
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  // Escキーで閉じる
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [isOpen]);

  const signalVariant = {
    bullish: "default" as const,
    bearish: "destructive" as const,
    neutral: "secondary" as const,
  };

  return (
    <div className="relative inline-block">
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="text-muted-foreground hover:text-foreground transition-colors p-0.5 rounded-full hover:bg-muted"
        aria-label={`${guide.nameJa}の説明を表示`}
      >
        <HelpCircle className="h-4 w-4" />
      </button>

      {isOpen && (
        <div
          ref={popoverRef}
          className="absolute z-50 top-full left-0 mt-2 w-72 rounded-lg border bg-popover p-4 shadow-lg"
        >
          {/* 矢印 */}
          <div className="absolute -top-2 left-3 w-4 h-4 rotate-45 border-l border-t bg-popover" />

          {/* ヘッダー */}
          <div className="relative">
            <h4 className="font-semibold text-sm">
              {guide.name}
              <span className="text-muted-foreground ml-1">({guide.nameJa})</span>
            </h4>

            {/* 概要 */}
            <p className="mt-2 text-sm text-muted-foreground">{guide.summary}</p>

            {/* 閾値 */}
            <div className="mt-3 space-y-1.5">
              <p className="text-xs font-medium text-muted-foreground">見方</p>
              {guide.thresholds.map((threshold, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between text-xs"
                >
                  <span className="font-mono">{threshold.range}</span>
                  <Badge variant={signalVariant[threshold.signal]} className="text-xs">
                    {threshold.label}
                  </Badge>
                </div>
              ))}
            </div>

            {/* 詳細リンク */}
            <Link
              href={`/guide#${indicatorId}`}
              className="mt-4 flex items-center gap-1 text-xs text-primary hover:underline"
              onClick={() => setIsOpen(false)}
            >
              詳しく見る <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
