import express from "express";
import multer from "multer"; // Third-party module for file uploads
import fs from "fs"; // Built-in module for file system operations
import path from "path";
import { fileURLToPath } from "url"; // Required for using __dirname in ES Modules

// Import the controller function using named export
import { uploadImage } from "./ImageController.js";

// --- ES Module Setup for pathing ---
// fileURLToPath and dirname are used to replicate the functionality of __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// Define the relative path to the folder for storing uploaded files
const uploadFolder = path.join(__dirname, "..", "screenshotsFolder"); // Adjusted path

// Create uploads folder if not exists
if (!fs.existsSync(uploadFolder)) {
  // fs.mkdirSync is a synchronous function to create the directory
  fs.mkdirSync(uploadFolder, { recursive: true });
}

// Setup multer storage
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    // cb(error, destination_path)
    cb(null, uploadFolder);
  },

  filename: function (req, file, cb) {
    // cb(error, filename)
    // Using the original filename as requested in the old code
    cb(null, file.originalname);
  },
});

// Initialize multer middleware with the storage configuration
const upload = multer({ storage });

// Route Definition:
// The 'upload.single("image")' middleware processes the form field named "image"
// and populates req.file before passing control to uploadImage.
router.post("/upload", upload.single("image"), uploadImage);

// Export the router for use in your main server file
export default router;
