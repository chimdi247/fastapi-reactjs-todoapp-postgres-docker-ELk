import { defineConfig } from 'vitest/config'

// Tests import the real sources from the frontend app (framework-free modules only).
export default defineConfig({
  test: { environment: 'jsdom', include: ['*.test.ts'], restoreMocks: true },
})
