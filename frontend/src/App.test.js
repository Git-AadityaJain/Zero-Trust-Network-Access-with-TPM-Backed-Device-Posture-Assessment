import { render } from '@testing-library/react';
import App from './App';

// Mock axios before importing App (which uses services that import axios)
jest.mock('axios', () => {
  const mockAxiosInstance = {
    get: jest.fn(() => Promise.resolve({ data: {} })),
    post: jest.fn(() => Promise.resolve({ data: {} })),
    patch: jest.fn(() => Promise.resolve({ data: {} })),
    put: jest.fn(() => Promise.resolve({ data: {} })),
    delete: jest.fn(() => Promise.resolve({ data: {} })),
    interceptors: {
      request: { use: jest.fn(), eject: jest.fn() },
      response: { use: jest.fn(), eject: jest.fn() },
    },
  };
  return {
    __esModule: true,
    default: {
      ...mockAxiosInstance,
      create: jest.fn(() => mockAxiosInstance),
    },
  };
});

test('renders app without crashing', () => {
  // Simple smoke test - just verify the app renders without errors
  const { container } = render(<App />);
  expect(container).toBeInTheDocument();
});
