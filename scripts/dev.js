/**
 * Zero-dependency cross-platform concurrent runner for IDMAP.
 * Runs FastAPI backend (port 8000) and React Vite frontend (port 5173) together.
 */

const { spawn } = require('child_process');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..');
const FRONTEND_DIR = path.resolve(ROOT_DIR, 'frontend');

const isWindows = process.platform === 'win32';
const npmCmd = isWindows ? 'npm.cmd' : 'npm';
const pythonCmd = isWindows ? 'python' : 'python3';

const colors = {
  reset: '\x1b[0m',
  cyan: '\x1b[36m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  bold: '\x1b[1m'
};

console.log(`${colors.cyan}${colors.bold}============================================================${colors.reset}`);
console.log(`${colors.green}${colors.bold}  IDMAP: Intelligent Disaster Mapping & Advisory Platform   ${colors.reset}`);
console.log(`${colors.cyan}${colors.bold}============================================================${colors.reset}`);
console.log(`Starting services:`);
console.log(`  • ${colors.cyan}Backend (FastAPI):${colors.reset}   http://localhost:8000 (Docs: http://localhost:8000/docs)`);
console.log(`  • ${colors.green}Frontend (Vite):${colors.reset}     http://localhost:5173`);
console.log(`Press Ctrl+C to terminate both processes.\n`);

function prefixStream(stream, prefix, color) {
  let buffer = '';
  stream.on('data', (chunk) => {
    buffer += chunk.toString();
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop(); // keep last incomplete line in buffer
    for (const line of lines) {
      if (line.trim()) {
        console.log(`${color}${prefix}${colors.reset} ${line}`);
      }
    }
  });
  stream.on('end', () => {
    if (buffer.trim()) {
      console.log(`${color}${prefix}${colors.reset} ${buffer}`);
    }
  });
}

// 1. Spawn Backend
const backend = spawn(pythonCmd, ['-m', 'uvicorn', 'backend.main:app', '--reload', '--port', '8000'], {
  cwd: ROOT_DIR,
  shell: true,
  env: { ...process.env, PYTHONUNBUFFERED: '1' }
});

prefixStream(backend.stdout, '[backend]', colors.cyan);
prefixStream(backend.stderr, '[backend]', colors.cyan);

// 2. Spawn Frontend
const frontend = spawn(npmCmd, ['run', 'dev'], {
  cwd: FRONTEND_DIR,
  shell: true
});

prefixStream(frontend.stdout, '[frontend]', colors.green);
prefixStream(frontend.stderr, '[frontend]', colors.green);

const processes = [backend, frontend];

function shutdown() {
  console.log(`\n${colors.yellow}Shutting down IDMAP services...${colors.reset}`);
  for (const proc of processes) {
    if (proc && !proc.killed) {
      if (isWindows && proc.pid) {
        try {
          spawn('taskkill', ['/pid', String(proc.pid), '/f', '/t']);
        } catch (_) {
          proc.kill('SIGTERM');
        }
      } else {
        proc.kill('SIGTERM');
      }
    }
  }
  process.exit(0);
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

backend.on('close', (code) => {
  if (code !== null && code !== 0) {
    console.log(`${colors.red}[backend] Process exited with code ${code}${colors.reset}`);
  }
});

frontend.on('close', (code) => {
  if (code !== null && code !== 0) {
    console.log(`${colors.red}[frontend] Process exited with code ${code}${colors.reset}`);
  }
});

