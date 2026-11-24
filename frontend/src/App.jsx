import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import Home from "./pages/Home.jsx";
import Orders from "./pages/Orders.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import { useLiveFeed } from "./services/api.js";

export default function App() {
    const feed = useLiveFeed();
    return (
        <>
            <Navbar connected={feed.connected} />
            <main>
                <Routes>
                    <Route path="/" element={<Home orders={feed.orders} />} />
                    <Route path="/orders" element={<Orders orders={feed.orders} />} />
                    <Route path="/dashboard" element={<Dashboard events={feed.events} assignments={feed.assignments} />} />
                    <Route path="*" element={<p className="empty">Page not found.</p>} />
                </Routes>
            </main>
        </>
    );
}
