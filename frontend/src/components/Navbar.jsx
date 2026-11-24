import { NavLink } from "react-router-dom";

export default function Navbar({ connected }) {
    const kafkaUi = `http://${location.hostname}:8080`;
    return (
        <header>
            <h1>🛒 Kafka Shop</h1>
            <nav>
                <NavLink to="/" end>Shop</NavLink>
                <NavLink to="/orders">Orders</NavLink>
                <NavLink to="/dashboard">Live Event Monitor</NavLink>
                <a href={kafkaUi} target="_blank" rel="noopener noreferrer">Kafka UI ↗</a>
                <span className="conn">
                    <span className={"dot" + (connected ? " on" : "")} />
                    {connected ? "Live" : "Reconnecting..."}
                </span>
            </nav>
        </header>
    );
}
