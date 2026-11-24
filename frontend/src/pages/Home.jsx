import OrderForm from "../components/OrderForm.jsx";
import OrderHistory from "../components/OrderHistory.jsx";

export default function Home({ orders }) {
    return (
        <>
            <OrderForm />
            <OrderHistory orders={orders.slice(0, 10)} />
        </>
    );
}
