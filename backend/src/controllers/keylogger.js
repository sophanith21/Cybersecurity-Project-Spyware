import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

export const saveToFile = (userId, data) => {
  const __filename = fileURLToPath(import.meta.url);
  const filePath = path.join(
    path.dirname(__filename),
    "..",
    "logs",
    userId + ".json"
  );
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
};

export const loadFromFile = (userId) => {
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
