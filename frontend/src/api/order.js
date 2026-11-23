import request from './index'

// 订单
export const getOrders = () => request.get('/orders')
export const payOrder = (id) => request.post(`/orders/${id}/pay`)
export const cancelOrder = (id) => request.post(`/orders/${id}/cancel`)
