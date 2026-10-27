// Start an isolated memory-book backend for Playwright without seeding personal data.
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const serverDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "server");
const testDataDir = mkdtempSync(path.join(os.tmpdir(), "memory-book-e2e-"));
const testDbPath = path.join(testDataDir, "memory_book.db");
const testUploadDir = path.join(testDataDir, "uploads");
const python = process.env.PYTHON || (process.platform === "win32" ? "py" : "python3");

const server = spawn(python, ["app.py"], {
  cwd: serverDir,
  env: {
    ...process.env,
    MEMORY_DATABASE_PATH: testDbPath,
    MEMORY_UPLOAD_DIR: testUploadDir,
    SECRET_KEY: "playwright-test-secret-only",
    FLASK_DEBUG: "false",
    FLASK_PORT: "5100",
    MIN_PASSWORD_LENGTH: "12",
    PUBLIC_DEPLOYMENT: "true",
    EPHEMERAL_STORAGE: "true",
  },
  stdio: "inherit",
});

server.on("error", (error) => {
  console.error("Could not start the test Flask server:", error.message);
  rmSync(testDataDir, { recursive: true, force: true });
  process.exitCode = 1;
});

server.on("close", (code) => {
  rmSync(testDataDir, { recursive: true, force: true });
  process.exit(code ?? 1);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => server.kill(signal));
}
