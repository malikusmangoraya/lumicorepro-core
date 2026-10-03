/**
 * filterStore — Zustand store for list filters (AGENTS.md §8: filters → Zustand).
 *
 * One slice per surface so the shop and the template hub never fight over the
 * same search box. Filters are session state: nothing is persisted.
 *
 * `selectFilterSlice(scope)` returns the slice object itself, whose reference only
 * changes when a filter changes — required because Zustand v5 compares snapshots
 * with `Object.is` (a selector that built a new object every call would loop).
 */
import { create } from 'zustand';

export const FILTER_SCOPES = {
  TEMPLATES: 'templates',
  SHOP: 'shop',
};

export const SORT_OPTIONS = {
  templates: [
    { value: 'featured', label: 'Featured' },
    { value: 'title', label: 'A → Z' },
    { value: 'category', label: 'Category' },
  ],
  shop: [
    { value: 'featured', label: 'Featured' },
    { value: 'price-asc', label: 'Price: low to high' },
    { value: 'price-desc', label: 'Price: high to low' },
    { value: 'rating', label: 'Top rated' },
  ],
};

const INITIAL_FILTERS = {
  [FILTER_SCOPES.TEMPLATES]: {
    search: '',
    category: 'All',
    sort: 'featured',
    maxPrice: null,
  },
  [FILTER_SCOPES.SHOP]: {
    search: '',
    category: 'all',
    sort: 'featured',
    maxPrice: null,
  },
};

export const useFilterStore = create((set) => ({
  ...Object.fromEntries(
    Object.entries(INITIAL_FILTERS).map(([scope, filters]) => [scope, { ...filters }])
  ),

  /** Update a single filter key inside one scope. */
  setFilter: (scope, key, value) =>
    set((state) => (state[scope] ? { [scope]: { ...state[scope], [key]: value } } : state)),

  /** Reset one scope back to its defaults. */
  resetFilters: (scope) =>
    set((state) =>
      INITIAL_FILTERS[scope] ? { [scope]: { ...INITIAL_FILTERS[scope] } } : state
    ),
}));

/** Reference-stable slice selector, e.g. `useFilterStore(selectFilterSlice('shop'))`. */
export const selectFilterSlice = (scope) => (state) => state[scope];

/** Action selector helper — `useFilterStore(selectFilterAction('setFilter'))`. */
export const selectFilterAction = (action) => (state) => state[action];

/* ── Pure filtering/sorting helpers shared by both surfaces ──────────────── */

/**
 * Apply search / category / price filters and sort order to a list.
 *
 * @param {Array}  items  — rows with the keys named by `fields`
 * @param {object} filters — a slice from this store
 * @param {object} fields  — { title, category, price, rating, tags, searchText }
 */
export const applyFilters = (items = [], filters = {}, fields = {}) => {
  const {
    title = 'title',
    category = 'category',
    price = 'price',
    rating = 'rating',
    tags = 'tags',
    searchText = 'description',
  } = fields;

  const query = String(filters.search || '')
    .trim()
    .toLowerCase();
  const activeCategory = filters.category;
  const maxPrice = filters.maxPrice;

  const filtered = items.filter((item) => {
    if (activeCategory && activeCategory !== 'all' && activeCategory !== 'All') {
      if (item[category] !== activeCategory) return false;
    }
    if (maxPrice != null && Number(item[price]) > maxPrice) return false;
    if (!query) return true;
    return (
      String(item[title] || '').toLowerCase().includes(query) ||
      String(item[searchText] || '').toLowerCase().includes(query) ||
      (item[tags] || []).some((tag) => String(tag).toLowerCase().includes(query))
    );
  });

  const sorted = [...filtered];
  switch (filters.sort) {
    case 'price-asc':
      sorted.sort((a, b) => Number(a[price]) - Number(b[price]));
      break;
    case 'price-desc':
      sorted.sort((a, b) => Number(b[price]) - Number(a[price]));
      break;
    case 'rating':
      sorted.sort((a, b) => Number(b[rating]) - Number(a[rating]));
      break;
    case 'title':
      sorted.sort((a, b) => String(a[title]).localeCompare(String(b[title])));
      break;
    case 'category':
      sorted.sort(
        (a, b) =>
          String(a[category]).localeCompare(String(b[category])) ||
          String(a[title]).localeCompare(String(b[title]))
      );
      break;
    default:
      break;
  }

  return sorted;
};

export default useFilterStore;
