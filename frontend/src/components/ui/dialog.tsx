"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import { Button } from "./button";
import { Icon } from "./icon";

export function Dialog({
  title,
  onClose,
  children,
  drawer,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  drawer?: "left" | "right";
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    const previous = document.activeElement;
    dialog?.showModal();
    return () => {
      dialog?.close();
      if (previous instanceof HTMLElement && previous.isConnected)
        previous.focus();
    };
  }, []);

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          const bounds = event.currentTarget.getBoundingClientRect();
          if (
            event.clientX < bounds.left ||
            event.clientX > bounds.right ||
            event.clientY < bounds.top ||
            event.clientY > bounds.bottom
          )
            onClose();
        }
      }}
      className={`no-print fixed border bg-surface p-0 text-foreground shadow-overlay backdrop:bg-overlay backdrop:backdrop-blur-sm ${drawer === "left" ? "inset-y-0 right-auto left-0 m-0 h-dvh max-h-dvh w-[18.125rem] max-w-[85vw]" : drawer === "right" ? "inset-y-0 right-0 left-auto m-0 ml-auto h-dvh max-h-dvh w-[26.5625rem] max-w-full" : "inset-0 m-auto max-h-[85dvh] w-[35rem] max-w-[calc(100vw-2rem)] rounded-dialog"}`}
    >
      <div className={`flex ${drawer ? "h-full" : "max-h-[85dvh]"} flex-col`}>
        <div className="flex shrink-0 items-center justify-between gap-3 border-b px-6 py-5">
          <h2 id={titleId} className="text-base font-semibold">
            {title}
          </h2>
          <Button
            variant="ghost"
            className="size-9 p-0!"
            onClick={onClose}
            aria-label="Zamknij okno"
          >
            <Icon name="close" />
          </Button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
      </div>
    </dialog>
  );
}
