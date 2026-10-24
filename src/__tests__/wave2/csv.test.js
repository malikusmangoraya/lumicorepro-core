import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { downloadBlob, downloadCSV, toCSV } from '../../utils/csv';

const readBlob = (blob) =>
  new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.readAsText(blob);
  });

const readBlobBytes = (blob) =>
  new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(new Uint8Array(reader.result));
    reader.readAsArrayBuffer(blob);
  });

let createObjectURL;
let revokeObjectURL;
let originalCreate;
let originalRevoke;
let clickSpy;
let clickedLink;

beforeEach(() => {
  originalCreate = URL.createObjectURL;
  originalRevoke = URL.revokeObjectURL;
  createObjectURL = vi.fn(() => 'blob:mock-url');
  revokeObjectURL = vi.fn();
  URL.createObjectURL = createObjectURL;
  URL.revokeObjectURL = revokeObjectURL;

  clickedLink = null;
  clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function () {
    clickedLink = this;
  });
});

afterEach(() => {
  clickSpy.mockRestore();
  if (originalCreate === undefined) delete URL.createObjectURL;
  else URL.createObjectURL = originalCreate;
  if (originalRevoke === undefined) delete URL.revokeObjectURL;
  else URL.revokeObjectURL = originalRevoke;
});

describe('toCSV', () => {
  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'qty', label: 'Qty' },
  ];

  it('writes escaped headers and rows separated by CRLF', () => {
    const csv = toCSV(
      [
        { name: 'Widget', qty: 2 },
        { name: 'Gadget', qty: 1 },
      ],
      columns
    );

    expect(csv).toBe('Name,Qty\r\nWidget,2\r\nGadget,1');
  });

  it('escapes commas, quotes, and newlines in cells', () => {
    const csv = toCSV(
      [
        { name: 'A, B', qty: 'He said "hi"' },
        { name: 'line\nbreak', qty: 'carriage\rreturn' },
      ],
      columns
    );

    expect(csv).toBe(
      'Name,Qty\r\n"A, B","He said ""hi"""\r\n"line\nbreak","carriage\rreturn"'
    );
  });

  it('renders null and undefined as empty cells', () => {
    const csv = toCSV([{ name: null, qty: undefined }], columns);

    expect(csv).toBe('Name,Qty\r\n,');
  });

  it('escapes header labels too', () => {
    const csv = toCSV([{ a: 1 }], [{ key: 'a', label: 'Amount, USD' }]);

    expect(csv).toBe('"Amount, USD"\r\n1');
  });

  it('returns only the header for an empty row set', () => {
    expect(toCSV([], columns)).toBe('Name,Qty');
  });

  it('coerces numbers and booleans to text', () => {
    const csv = toCSV(
      [{ name: 0, qty: true }, { name: false, qty: 3.5 }],
      [
        { key: 'name', label: 'Name' },
        { key: 'qty', label: 'Qty' },
      ]
    );

    expect(csv).toBe('Name,Qty\r\n0,true\r\nfalse,3.5');
  });
});

describe('downloadCSV', () => {
  it('downloads a UTF-8 CSV blob with a BOM', async () => {
    downloadCSV('Name,Qty\r\nWidget,2', 'products.csv');

    expect(createObjectURL).toHaveBeenCalledTimes(1);
    const blob = createObjectURL.mock.calls[0][0];
    expect(blob.type).toBe('text/csv;charset=utf-8;');

    const bytes = await readBlobBytes(blob);
    expect([...bytes.slice(0, 3)]).toEqual([0xef, 0xbb, 0xbf]);
    expect(new TextDecoder().decode(bytes.slice(3))).toBe('Name,Qty\r\nWidget,2');

    expect(clickedLink.download).toBe('products.csv');
    expect(clickedLink.href).toContain('blob:mock-url');
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
  });

  it('cleans the temporary anchor out of the document', () => {
    downloadCSV('a,b', 'file.csv');

    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(document.querySelectorAll('a')).toHaveLength(0);
  });
});

describe('downloadBlob', () => {
  it('wraps raw data in a blob with the requested MIME type', async () => {
    const buffer = new TextEncoder().encode('id,name\n1,Widget');
    downloadBlob(buffer, 'raw.csv', 'text/csv;charset=utf-8');

    const blob = createObjectURL.mock.calls[0][0];
    expect(blob.type).toBe('text/csv;charset=utf-8');
    await expect(readBlob(blob)).resolves.toBe('id,name\n1,Widget');
    expect(clickedLink.download).toBe('raw.csv');
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
  });

  it('defaults to the CSV MIME type', () => {
    downloadBlob('a,b', 'export.csv');

    expect(createObjectURL.mock.calls[0][0].type).toBe('text/csv;charset=utf-8');
  });
});
