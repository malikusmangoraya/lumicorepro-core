exports.getAll = async (req, res) => {
  res.json({ success: true, data: [] });
};

exports.create = async (req, res) => {
  res.status(201).json({ success: true, message: 'Item created', data: req.body });
};
