import { defineConfig, devices } from "@playwright/test";

// Backend is a Python venv; pick the right interpreter path per-OS so
// `npm run test:e2e` boots both servers with no manual steps. On Windows the
// command runs via cmd.exe, which needs backslash paths at the command token.
const isWin = process.platform === "win32";
const python = isWin
  ? "..\\backend\\.venv\\Scripts\\python.exe"
  : "../backend/.venv/bin/python";
const appDir = isWin ? "..\\backend" : "../backend";
const backendCmd =
  `${python} -m uvicorn app.main:app --app-dir ${appDir} --port 8000 --log-level warning`;

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  // Playwright starts these if not already up; reuses running ones locally.
  webServer: [
    {
      command: backendCmd,
      url: "http://localhost:8000/api/health",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      command: "npm run dev",
      url: "http://localhost:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
