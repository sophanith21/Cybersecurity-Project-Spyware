const { read } = require("fs");
const path = require("path");

// This function handles the image upload logic
exports.uploadImage = (req, res) => {
  if (!req.file) return res.status(400).send("No file uploaded");
  res.send({ message: "File uploaded successfully", filename: req.file.filename });

  
};
