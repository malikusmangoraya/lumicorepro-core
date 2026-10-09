/**
 * Client-state store wrapper (Zustand).
 * Platform TRD: lightweight store wrapper for UI/fragment state —
 * server state stays in the React Query cache cluster.
 */
import { create } from 'zustand';

export const useAppStore = create((set) => ({
  ui: { sidebarOpen: false },
  toggleSidebar: () => set((s) => ({ ui: { ...s.ui, sidebarOpen: !s.ui.sidebarOpen } })),
  cart: [],
  addItem: (item) => set((s) => ({ cart: [...s.cart, item] })),
  removeItem: (id) => set((s) => ({ cart: s.cart.filter((i) => i.id !== id) })),
  clearCart: () => set({ cart: [] }),
}));

export default useAppStore;
