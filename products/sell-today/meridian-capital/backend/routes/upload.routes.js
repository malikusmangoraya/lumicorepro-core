import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { protect } from '../middleware/auth.js';
import { uploadLimiter } from '../middleware/rateLimit.js';
import logger from '../utils/logger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// Ensure upload directory exists
const uploadDir = path.join(__dirname, '..', 'uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// Multer storage configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    const cleanName = path.basename(file.originalname, ext).replace(/[^a-zA-Z0-9]/g, '_');
    const uniqueSuffix = `${Date.now()}-${Math.round(Math.random() * 1e9)}`;
    cb(null, `${cleanName}-${uniqueSuffix}${ext}`);
  },
});

// File filter validation
const fileFilter = (req, file, cb) => {
  const allowedTypes = /jpeg|jpg|png|gif|webp|svg|pdf|mp4/;
  const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
  const mimetype = allowedTypes.test(file.mimetype);

  if (extname && mimetype) {
    cb(null, true);
  } else {
    cb(new Error('Only image, PDF, and video files are supported!'), false);
  }
};

const upload = multer({
  storage,
  limits: {
    fileSize: parseInt(process.env.MAX_FILE_SIZE, 10) || 10 * 1024 * 1024, // 10MB default
  },
  fileFilter,
});

/**
 * @swagger
 * /api/uploads/single:
 *   post:
 *     summary: Upload a single file
 *     tags: [Uploads]
 *     security:
 *       - bearerAuth: []
 */
router.post('/single', protect, uploadLimiter, upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ success: false, error: 'Please upload a file' });
  }

  const fileUrl = `/uploads/${req.file.filename}`;

  logger.info(`File uploaded: ${req.file.filename} (${req.file.size} bytes) by ${req.user.email}`);

  res.status(201).json({
    success: true,
    file: {
      filename: req.file.filename,
      originalName: req.file.originalname,
      mimetype: req.file.mimetype,
      size: req.file.size,
      url: fileUrl,
    },
  });
});

/**
 * @swagger
 * /api/uploads/multiple:
 *   post:
 *     summary: Upload multiple files (up to 10)
 *     tags: [Uploads]
 *     security:
 *       - bearerAuth: []
 */
router.post('/multiple', protect, uploadLimiter, upload.array('files', 10), (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ success: false, error: 'Please upload at least one file' });
  }

  const files = req.files.map((file) => ({
    filename: file.filename,
    originalName: file.originalname,
    mimetype: file.mimetype,
    size: file.size,
    url: `/uploads/${file.filename}`,
  }));

  logger.info(`${files.length} files uploaded by ${req.user.email}`);

  res.status(201).json({
    success: true,
    count: files.length,
    files,
  });
});

/**
 * @swagger
 * /api/uploads/{filename}:
 *   delete:
 *     summary: Delete an uploaded file
 *     tags: [Uploads]
 *     security:
 *       - bearerAuth: []
 */
router.delete('/:filename', protect, (req, res) => {
  const filePath = path.join(uploadDir, path.basename(req.params.filename));

  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ success: false, error: 'File not found' });
  }

  fs.unlink(filePath, (err) => {
    if (err) {
      logger.error(`Error deleting file ${req.params.filename}: ${err.message}`);
      return res.status(500).json({ success: false, error: 'Failed to delete file' });
    }

    res.json({
      success: true,
      message: 'File deleted successfully',
    });
  });
});

export default router;
