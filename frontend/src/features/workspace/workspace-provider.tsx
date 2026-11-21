"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useState,
  type ReactNode,
} from "react";
import { createAssessment, createWorkspace } from "@/features/assessments/model/defaults";
import type { Assessment, EmployeeId, WorkspaceState } from "@/features/assessments/model/types";
import { parseWorkspace, serializeWorkspace, storageKey } from "./storage";

type Action =
  | { type: "restore"; state: WorkspaceState; error?: string }
  | {
      type: "update";
      id: EmployeeId;
      update: (assessment: Assessment) => Assessment;
    }
  | { type: "theme" }
  | { type: "reset" };

interface Store {
  data: WorkspaceState;
  ready: boolean;
  error: string | null;
}

function reducer(store: Store, action: Action): Store {
  switch (action.type) {
    case "restore":
      return { data: action.state, ready: true, error: action.error ?? null };
    case "update":
      return {
        ...store,
        data: {
          ...store.data,
          assessments: {
            ...store.data.assessments,
            [action.id]: action.update(store.data.assessments[action.id]),
          },
        },
      };
    case "theme":
      return {
        ...store,
        data: {
          ...store.data,
          theme: store.data.theme === "light" ? "dark" : "light",
        },
      };
    case "reset":
      return { ...store, data: createWorkspace(), error: null };
  }
}

interface WorkspaceContextValue {
  state: WorkspaceState;
  ready: boolean;
  updateAssessment: (
    id: EmployeeId,
    update: Partial<Assessment> | ((assessment: Assessment) => Assessment),
  ) => void;
  startAssessment: (id: EmployeeId) => void;
  toggleTheme: () => void;
  reset: () => void;
  notify: (message: string) => void;
  openAssistant: () => void;
  closeAssistant: () => void;
  assistantOpen: boolean;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [store, dispatch] = useReducer(reducer, undefined, () => ({
    data: createWorkspace(),
    ready: false,
    error: null,
  }));
  const [storageError, setStorageError] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [assistantOpen, setAssistantOpen] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      const saved = raw ? parseWorkspace(raw) : null;
      dispatch({
        type: "restore",
        state: saved ?? createWorkspace(),
        error:
          raw && !saved
            ? "Nie udało się odczytać danych lokalnych. Przywrócono dane demonstracyjne."
            : undefined,
      });
    } catch {
      dispatch({
        type: "restore",
        state: createWorkspace(),
        error: "Zapis lokalny jest niedostępny. Zmiany pozostaną tylko w tej sesji.",
      });
    }
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = store.data.theme;
    if (!store.ready) return;
    try {
      localStorage.setItem(storageKey, serializeWorkspace(store.data));
    } catch {
      queueMicrotask(() =>
        setStorageError(
          "Nie udało się zapisać zmian lokalnie. Nie zamykaj karty, jeśli chcesz je zachować.",
        ),
      );
    }
  }, [store.data, store.ready]);

  useEffect(() => {
    if (!message) return;
    const timer = window.setTimeout(() => setMessage(""), 3300);
    return () => window.clearTimeout(timer);
  }, [message]);

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      state: store.data,
      ready: store.ready,
      updateAssessment: (id, update) =>
        dispatch({
          type: "update",
          id,
          update:
            typeof update === "function" ? update : (assessment) => ({ ...assessment, ...update }),
        }),
      startAssessment: (id) => dispatch({ type: "update", id, update: () => createAssessment() }),
      toggleTheme: () => dispatch({ type: "theme" }),
      reset: () => {
        dispatch({ type: "reset" });
        setAssistantOpen(false);
        setMessage("Przywrócono dane demo.");
      },
      notify: setMessage,
      assistantOpen,
      openAssistant: () => setAssistantOpen(true),
      closeAssistant: () => setAssistantOpen(false),
    }),
    [store.data, store.ready, assistantOpen],
  );

  return (
    <WorkspaceContext.Provider value={value}>
      {store.error || storageError ? (
        <p
          role="alert"
          className="no-print border-b bg-warning-muted px-5 py-3 text-body text-warning"
        >
          {storageError ?? store.error}
        </p>
      ) : null}
      {children}
      <div aria-live="polite" aria-atomic="true" className="no-print">
        {message ? (
          <div className="fixed bottom-6 left-1/2 z-100 max-w-[calc(100vw-2rem)] -translate-x-1/2 rounded-xl bg-toast px-5 py-3 text-body text-white shadow-toast">
            {message}
          </div>
        ) : null}
      </div>
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error("WorkspaceProvider is required.");
  return context;
}
