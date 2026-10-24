import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import useInspector from '../../hooks/useInspector';

function createFrame() {
  const posted = [];
  const appended = [];
  const doc = {
    getElementById: vi.fn(() => null),
    createElement: vi.fn(() => ({ id: '', textContent: '' })),
    body: {
      appendChild: vi.fn((node) => {
        appended.push(node);
        return node;
      }),
    },
  };
  const view = {
    postMessage: vi.fn((message) => posted.push(message)),
    document: doc,
  };
  return { frame: { contentWindow: view, contentDocument: doc }, posted, appended, doc };
}

let harness;
let frameRef;

beforeEach(() => {
  harness = createFrame();
  frameRef = { current: harness.frame };
});

function dispatchMessage(data) {
  act(() => {
    window.dispatchEvent(new MessageEvent('message', { data }));
  });
}

describe('useInspector', () => {
  it('exposes the documented initial state and stops inspection on mount', () => {
    const { result } = renderHook(() => useInspector(frameRef));

    expect(result.current).toMatchObject({
      inspectMode: false,
      selectedElement: null,
      hoveredElement: null,
    });
    expect(typeof result.current.toggleInspect).toBe('function');
    expect(harness.posted).toContainEqual({ type: 'LUMI_STOP_INSPECT' });
  });

  it('injects the inspector script and toggles inspect mode in the iframe', () => {
    const { result } = renderHook(() => useInspector(frameRef));

    act(() => result.current.toggleInspect());

    expect(result.current.inspectMode).toBe(true);
    expect(harness.posted).toContainEqual(
      expect.objectContaining({ type: 'LUMI_INJECT_SCRIPT', script: expect.any(String) })
    );
    expect(harness.posted).toContainEqual({ type: 'LUMI_TOGGLE_INSPECT' });
    expect(harness.appended).toHaveLength(1);
    expect(harness.appended[0].id).toBe('__lumi_inspector__');
    expect(harness.appended[0].textContent).toContain('__LUMI_INSPECTOR__');

    act(() => result.current.toggleInspect());
    expect(result.current.inspectMode).toBe(false);
    expect(harness.posted).toContainEqual({ type: 'LUMI_STOP_INSPECT' });
  });

  it('stores element selections received from the iframe', () => {
    const { result } = renderHook(() => useInspector(frameRef));
    const payload = {
      component: 'HeroSection',
      domPath: 'section > h1',
      tag: 'h1',
      rect: { x: 0, y: 0, width: 100, height: 40 },
    };

    dispatchMessage({ type: 'LUMI_ELEMENT_SELECTED', payload });

    expect(result.current.selectedElement).toEqual(payload);
  });

  it('follows inspect-mode messages and clears the selection when disabled', () => {
    const { result } = renderHook(() => useInspector(frameRef));

    dispatchMessage({ type: 'LUMI_ELEMENT_SELECTED', payload: { component: 'Card' } });
    expect(result.current.selectedElement).toEqual({ component: 'Card' });

    dispatchMessage({ type: 'LUMI_INSPECT_MODE', payload: { active: true } });
    expect(result.current.inspectMode).toBe(true);

    dispatchMessage({ type: 'LUMI_INSPECT_MODE', payload: { active: false } });
    expect(result.current.inspectMode).toBe(false);
    expect(result.current.selectedElement).toBeNull();
  });

  it('ignores unrelated messages and clears a selection on demand', () => {
    const { result } = renderHook(() => useInspector(frameRef));

    dispatchMessage({ type: 'SOMETHING_ELSE', payload: {} });
    expect(result.current.selectedElement).toBeNull();

    dispatchMessage({ type: 'LUMI_ELEMENT_SELECTED', payload: { component: 'Nav' } });
    act(() => result.current.clearSelection());

    expect(result.current.selectedElement).toBeNull();
  });
});
