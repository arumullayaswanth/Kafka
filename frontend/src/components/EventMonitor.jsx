import { dash, money } from "../services/api.js";

const GROUPS = [
    { id: "order-processing-group", label: "Order Processing" },
    { id: "payment-processing-group", label: "Payment Processing" },
    { id: "notification-group", label: "Notification" },
];
const PARTITIONS = [0, 1, 2];

// Partition -> consumer table for each group, read from Kafka by the backend every 3 s.
function Assignments({ assignments }) {
    return (
        <section className="card">
            <h2>Consumer groups and partition assignment</h2>
            <div className="groups">
                {GROUPS.map((g) => {
                    const members = assignments[g.id] || {};
                    const owner = (p) => Object.keys(members).find((c) => members[c].includes(p));
                    return (
                        <div key={g.id} className="group">
                            <div className="group-title">{g.label}</div>
                            <div className="group-id">{g.id} · {Object.keys(members).length} active</div>
                            {PARTITIONS.map((p) => (
                                <div key={p} className="assign">
                                    <span className="pill">P{p}</span>
                                    <span className={owner(p) ? "" : "muted"}>{owner(p) || "unassigned"}</span>
                                </div>
                            ))}
                        </div>
                    );
                })}
            </div>
        </section>
    );
}

export default function EventMonitor({ events, assignments }) {
    return (
        <>
            <Assignments assignments={assignments} />
            <section className="card">
                <h2>Live Kafka Events</h2>
                <div className="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Order ID</th><th>Name</th><th>Product</th><th>Amount</th><th>Event status</th>
                                <th>Group</th><th>Consumer</th><th>Partition</th><th>Offset</th><th>Timestamp</th>
                            </tr>
                        </thead>
                        <tbody>
                            {events.length === 0 && (
                                <tr><td colSpan={10} className="empty">Waiting for events...</td></tr>
                            )}
                            {events.map((e, i) => (
                                <tr key={`${e.order_id}-${e.event_status}-${i}`}>
                                    <td>{e.order_id}</td>
                                    <td>{e.customer_name}</td>
                                    <td>{e.product}</td>
                                    <td>{money(e.amount)}</td>
                                    <td><span className={"badge b-" + e.event_status}>{e.event_status}</span></td>
                                    <td>{dash(e.group)}</td>
                                    <td>{dash(e.consumer)}</td>
                                    <td>{dash(e.partition)}</td>
                                    <td>{dash(e.offset)}</td>
                                    <td>{new Date(e.timestamp).toLocaleTimeString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>
        </>
    );
}
