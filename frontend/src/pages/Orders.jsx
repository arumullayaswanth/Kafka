import OrderHistory from "../components/OrderHistory.jsx";

export default function Orders({ orders }) {
    return <OrderHistory orders={orders} title="Order History" />;
}
