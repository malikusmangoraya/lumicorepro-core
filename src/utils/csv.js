/**
 * CSV export helpers — client-side, UTF-8 (with BOM for Excel) safe.
 */
const sanitizeCell = (value) => {
  if (value === null || value === undefined) return '';
  const str = String(value);
  if (/[",\n\r]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
};

/**
 * Build a CSV string from an array of objects.
 * @param {Array<Object>} rows
 * @param {Array<{key: string, label: string}>} columns
 */
export const toCSV = (rows, columns) => {
  const header = columns.map((c) => sanitizeCell(c.label)).join(',');
  const body = rows.map((row) =>
    columns.map((c) => sanitizeCell(row[c.key])).join(',')
  );
  return [header, ...body].join('\r\n');
};

/**
 * Serialize a Blob/ArrayBuffer to CSV and trigger a browser download.
 */
export const downloadCSV = (csv, filename) => {
  const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Export raw response data (e.g. an ArrayBuffer from the backend) as a file.
 */
export const downloadBlob = (blob, filename, mime = 'text/csv;charset=utf-8') => {
  const url = URL.createObjectURL(new Blob([blob], { type: mime }));
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};