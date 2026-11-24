import { dash, money } from "../services/api.js";

const LABEL = {
    PROCESSED: "Processed",
    PAYMENT_CONFIRMED: "Paid",
    NOTIFICATION_SENT: "Notified",
    PENDING: "Pending",
    PUBLISHED: "Published",
    PUBLISHING: "Publishing",
    FAILED: "Failed",
};

const Stage = ({ value, by }) => (
    <>
        <span className={"badge b-" + value} title={value}>{LABEL[value] || value}</span>
        {by && <div className="by">{by}</div>}
    </>
);

export default function OrderHistory({ orders, title = "Recent Orders" }) {
    return (
        <section className="card">
            <h2>{title}</h2>
            <p className="hint">
                Every order is read by all three consumer groups independently. Each status column is updated by a different group.
            </p>
            <div className="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Order ID</th><th>Name</th><th>Items</th><th>Amount</th><th>Partition / Offset</th>
                            <th>Order processing</th><th>Payment</th><th>Notification</th><th>Placed</th>
                        </tr>
                    </thead>
                    <tbody>
                        {orders.length === 0 && (
                            <tr><td colSpan={9} className="empty">No orders yet. Place one on the Shop page.</td></tr>
                        )}
                        {orders.map((o) => {
                            const by = o.processed_by || {};
                            return (
                                <tr key={o.order_id}>
                                    <td>{o.order_id}</td>
                                    <td>{o.customer_name}</td>
                                    <td>{o.product}</td>
                                    <td>{money(o.amount)}</td>
                                    <td>P{dash(o.partition)} / {dash(o.offset)}</td>
                                    <td><Stage value={o.status} by={by["order-processing-group"]} /></td>
                                    <td><Stage value={o.payment_status || "PENDING"} by={by["payment-processing-group"]} /></td>
                                    <td><Stage value={o.notification_status || "PENDING"} by={by["notification-group"]} /></td>
                                    <td>{new Date(o.created_at).toLocaleTimeString()}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </section>
    );
}
