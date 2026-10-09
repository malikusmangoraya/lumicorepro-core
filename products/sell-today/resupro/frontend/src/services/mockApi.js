/**
 * Static API mock handlers — client-only showcase mode.
 * Promise-based stand-ins for backend data so the SPA renders and
 * state/filter interactions work with zero server hosting.
 */
const delay = (ms = 220) => new Promise((resolve) => setTimeout(resolve, ms));

const COLLECTIONS = {
  products: [
    { id: 1, title: 'Signature Package', tagline: 'Hero offering', price: 149 },
    { id: 2, title: 'Growth Package', tagline: 'Best seller', price: 249 },
    { id: 3, title: 'Premium Package', tagline: 'Full-service', price: 499 },
  ],
  testimonials: [
    { id: 1, name: 'Ayesha Khan', text: 'Outstanding quality and support.' },
    { id: 2, name: 'Omar Farooq', text: 'Modern, fast and beautiful.' },
    { id: 3, name: 'Sarah Malik', text: 'Exceeded every expectation.' },
  ],
  gallery: [
    { id: 1, title: 'Project One' },
    { id: 2, title: 'Project Two' },
    { id: 3, title: 'Project Three' },
  ],
};

export const getMockCollection = async (collection, query = {}) => {
  await delay();
  const items = [...(COLLECTIONS[collection] || [])];
  if (query.q)
    return items.filter((i) =>
      JSON.stringify(i).toLowerCase().includes(String(query.q).toLowerCase())
    );
  if (query.limit) return items.slice(0, Number(query.limit));
  return items;
};

export const postMockRecord = async (collection, payload) => {
  await delay();
  return { ok: true, id: `${collection}-${Date.now()}`, ...payload };
};
