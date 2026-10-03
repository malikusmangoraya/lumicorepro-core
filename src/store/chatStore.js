/**
 * chatStore — Zustand store for chat transcripts (AGENTS.md §8: chat → Zustand).
 *
 * Holds the conversation plus the two flags the UI needs to render progress:
 * `pending` (a request is in flight) and `streaming` (tokens are arriving).
 * Deliberately not persisted: transcripts can contain uploaded documents and
 * pasted business content, so they must not land in localStorage.
 */
import { create } from 'zustand';

const INITIAL_STATE = {
  messages: [],
  pending: false,
  streaming: false,
};

export const useChatStore = create((set) => ({
  ...INITIAL_STATE,

  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),

  /** Patch one message — used for streaming deltas and to clear error flags. */
  updateMessage: (id, patch) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, ...(typeof patch === 'function' ? patch(m) : patch) } : m
      ),
    })),

  removeMessage: (id) =>
    set((state) => ({ messages: state.messages.filter((m) => m.id !== id) })),

  /** Replace the whole transcript (e.g. loading a previous conversation). */
  setMessages: (messages) => set({ messages: messages || [] }),

  setPending: (pending) => set({ pending: Boolean(pending) }),

  setStreaming: (streaming) => set({ streaming: Boolean(streaming) }),

  reset: () => set({ ...INITIAL_STATE }),
}));

/* ── Selectors (`state => state.property` pattern) ───────────────────────── */
export const selectMessages = (state) => state.messages;
export const selectPending = (state) => state.pending;
export const selectStreaming = (state) => state.streaming;
export const selectIsBusy = (state) => state.pending || state.streaming;

export default useChatStore;
