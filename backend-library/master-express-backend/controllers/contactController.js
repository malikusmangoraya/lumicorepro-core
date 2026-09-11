const validator = require('validator');
const { Contact } = require('../models/Contact');
const { Op } = require('sequelize');

// @desc    Submit contact form
// @route   POST /api/contact
// @access  Public
exports.submitContact = async (req, res, next) => {
  try {
    const { name, email, subject, message, phone } = req.body;

    // Validation
    if (!name || !email || !subject || !message) {
      return res.status(400).json({
        success: false,
        message: 'Please provide all required fields'
      });
    }

    if (!validator.isEmail(email)) {
      return res.status(400).json({
        success: false,
        message: 'Please provide a valid email'
      });
    }

    // Save to database
    const contact = await Contact.create({
      name,
      email,
      subject,
      message,
      phone
    });

    console.log('Contact Form Submission saved to DB:', contact.id);

    res.status(201).json({
      success: true,
      message: 'Thank you for contacting us! We will get back to you soon.',
      data: { id: contact.id }
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get all contact messages (admin)
// @route   GET /api/contact
// @access  Private (Admin)
exports.getAllContacts = async (req, res, next) => {
  try {
    const { page = 1, limit = 10, sortBy = 'createdAt', order = 'DESC' } = req.query;
    
    const offset = (page - 1) * limit;
    
    const { count, rows } = await Contact.findAndCountAll({
      where: req.query.isRead !== undefined ? { isRead: req.query.isRead === 'true' } : undefined,
      order: [[sortBy, order]],
      limit: parseInt(limit),
      offset: parseInt(offset)
    });

    res.json({
      success: true,
      data: {
        contacts: rows,
        pagination: {
          total: count,
          page: parseInt(page),
          pages: Math.ceil(count / limit)
        }
      }
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get single contact message
// @route   GET /api/contact/:id
// @access  Private (Admin)
exports.getContactById = async (req, res, next) => {
  try {
    const contact = await Contact.findByPk(req.params.id);
    
    if (!contact) {
      return res.status(404).json({
        success: false,
        message: 'Contact message not found'
      });
    }

    // Mark as read
    if (!contact.isRead) {
      contact.isRead = true;
      await contact.save();
    }

    res.json({
      success: true,
      data: { contact }
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Mark contact as replied
// @route   PUT /api/contact/:id/reply
// @access  Private (Admin)
exports.markAsReplied = async (req, res, next) => {
  try {
    const contact = await Contact.findByPk(req.params.id);
    
    if (!contact) {
      return res.status(404).json({
        success: false,
        message: 'Contact message not found'
      });
    }

    contact.isReplied = true;
    contact.isRead = true;
    await contact.save();

    res.json({
      success: true,
      message: 'Contact marked as replied',
      data: { contact }
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Delete contact message
// @route   DELETE /api/contact/:id
// @access  Private (Admin)
exports.deleteContact = async (req, res, next) => {
  try {
    const contact = await Contact.findByPk(req.params.id);
    
    if (!contact) {
      return res.status(404).json({
        success: false,
        message: 'Contact message not found'
      });
    }

    await contact.destroy();

    res.json({
      success: true,
      message: 'Contact message deleted'
    });
  } catch (error) {
    next(error);
  }
};
      message: 'Thank you for contacting us! We will get back to you soon.'
    });
  } catch (error) {
    next(error);
  }
};