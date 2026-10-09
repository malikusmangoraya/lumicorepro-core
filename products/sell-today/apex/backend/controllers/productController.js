exports.getAll = async (req, res) => {
  res.json({
    success: true,
    count: 3,
    data: [
      { id: 1, name: 'Sample Item Alpha', price: 99.99, category: 'Electronics', stock: 25 },
      { id: 2, name: 'Sample Item Beta', price: 149.99, category: 'Gadgets', stock: 10 },
      { id: 3, name: 'Sample Item Gamma', price: 49.99, category: 'Accessories', stock: 50 },
    ],
  });
};

exports.getById = async (req, res) => {
  res.json({ success: true, data: { id: req.params.id, name: 'Sample Item', price: 99.99 } });
};

exports.create = async (req, res) => {
  res.status(201).json({ success: true, message: 'Created successfully', data: req.body });
};
