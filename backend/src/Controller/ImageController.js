import path from "path";
// Note: 'read' is not necessary for this function, so it's removed for clean code.

/**
 * Handles the image upload logic after multer has processed the file.
 * @param {object} req - Express request object (contains req.file from multer)
 * @param {object} res - Express response object
 */
export const uploadImage = (req, res) => {
  // req.file is populated by multer middleware
  if (!req.file) {
    // You might want to log this error
    return res.status(400).send({ error: "No file uploaded" });
  }

  // The filename is set by the storage configuration in the router file
  res.send({
    message: "File uploaded successfully",
    filename: req.file.filename,
  });
};
