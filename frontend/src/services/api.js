import { useEffect, useRef, useState } from "react";

export const money = (n) => "₹" + Number(n).toLocaleString("en-IN");
export const dash = (v) => (v === null || v === undefined ? "-" : v);

export async function getProducts() {
    const res = await fetch("/api/products");
    if (!res.ok) throw new Error("could not load products");
    return res.json();
}

export async function placeOrder(customer_name, items) {
    const res = await fetch("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ customer_name, items }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        const d = data.detail;
        throw new Error(Array.isArray(d) ? d.map((x) => x.msg).join("; ") : d || `HTTP ${res.status}`);
    }
    return data;
}

export function useLiveFeed() {
    const [orders, setOrders] = useState([]);
    const [events, setEvents] = useState([]);
    const [assignments, setAssignments] = useState({});
    const [connected, setConnected] = useState(false);
    const closed = useRef(false);

    useEffect(() => {
        closed.current = false;
        let ws;
        let timer;
        let ping;

        const connect = () => {
            const proto = location.protocol === "https:" ? "wss" : "ws";
            ws = new WebSocket(`${proto}://${location.host}/ws`);
            ws.onopen = () => {
                setConnected(true);
                ping = setInterval(() => ws.readyState === 1 && ws.send("ping"), 25000);
            };
            ws.onmessage = (e) => {
                const m = JSON.parse(e.data);
                if (m.type === "snapshot") {
                    setOrders(m.orders);
                    setEvents(m.events);
                    setAssignments(m.assignments || {});
                } else if (m.type === "update") {
                    setOrders((prev) =>
                        prev.some((o) => o.order_id === m.order.order_id)
                            ? prev.map((o) => (o.order_id === m.order.order_id ? m.order : o))
                            : [m.order, ...prev].slice(0, 50)
                    );
                    setEvents((prev) => [m.event, ...prev].slice(0, 150));
                } else if (m.type === "assignments") {
                    setAssignments(m.assignments);
                }
            };
            ws.onclose = () => {
                setConnected(false);
                clearInterval(ping);
                if (!closed.current) timer = setTimeout(connect, 2000);
            };
        };
        connect();

        return () => {
            closed.current = true;
            clearTimeout(timer);
            clearInterval(ping);
            ws && ws.close();
        };
    }, []);

    return { orders, events, assignments, connected };
}
