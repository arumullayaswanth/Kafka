import EventMonitor from "../components/EventMonitor.jsx";

export default function Dashboard({ events, assignments }) {
    return <EventMonitor events={events} assignments={assignments} />;
}
