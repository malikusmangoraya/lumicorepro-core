exports.createOrder = async (req, res) => {
  res.status(201).json({
    success: true,
    message: 'Order created',
    orderId: 'ORD-' + Date.now(),
    items: req.body.items,
  });
};

exports.getUserOrders = async (req, res) => {
  res.json({ success: true, orders: [] });
};
