import '@testing-library/jest-dom'
import { vi, beforeAll, afterAll } from 'vitest'
import { act } from '@testing-library/react'

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock window.confirm
global.confirm = () => true

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn((key: string) => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(() => null),
}

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
})

// Mock URL.createObjectURL and URL.revokeObjectURL
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
global.URL.revokeObjectURL = vi.fn()

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn()

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return []
  }
  unobserve() {}
} as any

// Mock React Router history
const createMockHistory = () => ({
  location: { pathname: '/', search: '', hash: '', state: null },
  replace: vi.fn(),
  push: vi.fn(),
  go: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  listen: vi.fn(() => vi.fn()),
  createHref: vi.fn(),
  replaceState: vi.fn(),
  pushState: vi.fn(),
})

// Mock global history for React Router
const mockHistory = {
  ...createMockHistory(),
  replaceState: vi.fn(),
  pushState: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  go: vi.fn(),
}

// Mock global history with React Router methods
Object.defineProperty(window, 'history', {
  value: {
    ...createMockHistory(),
    replaceState: vi.fn(),
    pushState: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    go: vi.fn(),
  },
  writable: true,
})

// Mock React Router's createBrowserHistory if used
vi.mock('history', () => ({
  createBrowserHistory: () => createMockHistory(),
}))

// Mock the globalHistory that React Router v6 uses
;(globalThis as any).globalHistory = {
  ...createMockHistory(),
  replaceState: vi.fn(),
  pushState: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  go: vi.fn(),
}

// Mock @remix-run/router which is used by React Router v6
vi.mock('@remix-run/router', () => {
  const mockHistory = {
    location: { pathname: '/', search: '', hash: '', state: null },
    replace: vi.fn(),
    push: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    listen: vi.fn(() => vi.fn()),
    createHref: vi.fn(),
    replaceState: vi.fn(),
    pushState: vi.fn(),
  };

  // Mock the globalHistory that's imported in the router
  const globalHistory = {
    ...mockHistory,
    replaceState: vi.fn(),
    pushState: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    go: vi.fn(),
  };

  return {
    createBrowserHistory: () => mockHistory,
    createMemoryHistory: () => mockHistory,
    globalHistory,
  };
});

// Also mock it on global scope as a fallback
;(globalThis as any).globalHistory = {
  location: { pathname: '/', search: '', hash: '', state: null },
  replace: vi.fn(),
  push: vi.fn(),
  go: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  listen: vi.fn(() => vi.fn()),
  createHref: vi.fn(),
  replaceState: vi.fn(),
  pushState: vi.fn(),
};

// Mock fetch to be a proper mock
const mockFetch = vi.fn()
global.fetch = mockFetch

// Default mock implementation
mockFetch.mockImplementation(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    blob: () => Promise.resolve(new Blob()),
  })
)

// Suppress console errors in tests (optional)
const originalError = console.error
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
        args[0].includes('Not implemented: HTMLFormElement.prototype.submit'))
    ) {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
})
