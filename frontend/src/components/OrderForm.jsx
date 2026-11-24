import { useEffect, useState } from "react";
import ProductCard from "./ProductCard.jsx";
import { getProducts, money, placeOrder } from "../services/api.js";

const NAME_OK = /^[A-Za-z0-9 .'_-]+$/;

export default function OrderForm() {
    const [products, setProducts] = useState([]);
    const [qty, setQty] = useState({});
    const [name, setName] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        getProducts()
            .then(setProducts)
            .catch((e) => setError(e.message));
    }, []);

    const total = products.reduce((s, p) => s + p.price * (qty[p.id] || 0), 0);
    const trimmed = name.trim();
    const nameInvalid = trimmed !== "" && !NAME_OK.test(trimmed);
    const canSubmit = total > 0 && trimmed !== "" && !nameInvalid && !busy;

    const submit = async () => {
        const items = products.filter((p) => qty[p.id] > 0).map((p) => ({ product_id: p.id, quantity: qty[p.id] }));
        setBusy(true);
        setError("");
        try {
            await placeOrder(trimmed, items);
            setQty({});
        } catch (e) {
            setError("Order rejected: " + e.message);
        } finally {
            setBusy(false);
        }
    };

    return (
        <section className="card">
            <h2>Products</h2>
            <div className="grid">
                {products.map((p) => (
                    <ProductCard key={p.id} product={p} quantity={qty[p.id] || 0} onChange={(n) => setQty({ ...qty, [p.id]: n })} />
                ))}
            </div>
            <div className="row">
                <div>
                    <label htmlFor="name">Your name</label>
                    <input
                        id="name"
                        type="text"
                        maxLength={50}
                        placeholder="Enter your name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && canSubmit && submit()}
                    />
                    {nameInvalid && <div className="field-err">Use letters, numbers, spaces and . ' _ - only</div>}
                </div>
                <div className="total">Total: {money(total)}</div>
                <button className="btn" disabled={!canSubmit} onClick={submit}>
                    {busy ? "Placing..." : "Place Order"}
                </button>
            </div>
            {error && <div className="msg err">{error}</div>}
        </section>
    );
}
