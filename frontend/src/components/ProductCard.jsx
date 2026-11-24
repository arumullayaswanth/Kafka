import { money } from "../services/api.js";

const ICONS = { laptop: "💻", smartphone: "📱", headphones: "🎧", keyboard: "⌨️", monitor: "🖥️" };

export default function ProductCard({ product, quantity, onChange }) {
    return (
        <div className="product">
            <div className="icon">{ICONS[product.id] || "📦"}</div>
            <div className="name">{product.name}</div>
            <div className="price">{money(product.price)}</div>
            <div className="qty">
                <button type="button" aria-label={`Remove one ${product.name}`} onClick={() => onChange(Math.max(0, quantity - 1))}>−</button>
                <span>{quantity}</span>
                <button type="button" aria-label={`Add one ${product.name}`} onClick={() => onChange(Math.min(10, quantity + 1))}>+</button>
            </div>
        </div>
    );
}
