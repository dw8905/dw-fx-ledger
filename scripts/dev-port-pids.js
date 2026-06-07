#!/usr/bin/env node

const fs = require("fs");

const port = Number(process.argv[2]);
if (!Number.isInteger(port) || port <= 0 || port > 65535) {
  process.exit(2);
}

const listenState = "0A";
const inodes = new Set();

for (const table of ["/proc/net/tcp", "/proc/net/tcp6"]) {
  let content;
  try {
    content = fs.readFileSync(table, "utf8");
  } catch {
    continue;
  }

  for (const line of content.trim().split("\n").slice(1)) {
    const columns = line.trim().split(/\s+/);
    const localAddress = columns[1] || "";
    const state = columns[3];
    const inode = columns[9];
    const [, localPortHex] = localAddress.split(":");
    if (!localPortHex || !inode || state !== listenState) {
      continue;
    }

    if (Number.parseInt(localPortHex, 16) === port) {
      inodes.add(inode);
    }
  }
}

if (inodes.size === 0) {
  process.exit(0);
}

const pids = new Set();
let procEntries = [];
try {
  procEntries = fs.readdirSync("/proc");
} catch {
  process.exit(0);
}

for (const entry of procEntries) {
  if (!/^\d+$/.test(entry)) {
    continue;
  }

  let fds = [];
  const fdDir = `/proc/${entry}/fd`;
  try {
    fds = fs.readdirSync(fdDir);
  } catch {
    continue;
  }

  for (const fd of fds) {
    let target;
    try {
      target = fs.readlinkSync(`${fdDir}/${fd}`);
    } catch {
      continue;
    }

    const match = /^socket:\[(\d+)\]$/.exec(target);
    if (match && inodes.has(match[1])) {
      pids.add(Number(entry));
      break;
    }
  }
}

console.log([...pids].sort((a, b) => a - b).join("\n"));
