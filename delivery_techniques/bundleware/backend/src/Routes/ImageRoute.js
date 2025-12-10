const express = require("express");
const router = express.Router();
const multer = require("multer"); // what is this?
const fs = require("fs");  // what is this?
const path = require("path");
const { uploadImage } = require("../Controller/ImageController");

// Create uploads folder if not exists
const uploadFolder = "./screenshotsFolder";
if (!fs.existsSync(uploadFolder)) fs.mkdirSync(uploadFolder);

// Setup multer storage
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, uploadFolder);
  },
  
  filename: function (req, file, cb) {

    cb(null, `${file.originalname}`); 
  },
});
const upload = multer({ storage });

// Route
router.post("/upload", upload.single("image"), uploadImage);

module.exports = router;
