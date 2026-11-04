/** stream — Server-Sent Events helpers for Express (typewriter AI output).
 * sseInit(res) flips headers; sseSend(res, event, data) frames one event;
 * sseStreamText(res, iterable, onDone) pipes AI deltas as `data:` frames.
 */
function sseInit(res) {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    Connection: 'keep-alive',
    'X-Accel-Buffering': 'no',
  });
  res.flushHeaders?.();
}

function sseSend(res, event, data) {
  res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
}

async function sseStreamText(res, textIterable, meta = {}) {
  sseInit(res);
  let full = '';
  try {
    for await (const delta of textIterable) {
      full += delta;
      sseSend(res, 'delta', { text: delta });
    }
    sseSend(res, 'done', { text: full, ...meta });
  } catch (err) {
    sseSend(res, 'error', { message: err.message || 'AI stream failed' });
  } finally {
    res.end();
  }
  return full;
}

module.exports = { sseInit, sseSend, sseStreamText };
