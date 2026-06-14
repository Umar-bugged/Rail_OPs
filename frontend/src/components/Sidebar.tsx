import { Activity, BarChart3, Gauge, Search, Server, TrainFront } from "lucide-react";
import { NavLink } from "react-router-dom";

const items = [
  { path: "/overview", label: "Overview", icon: Activity },
  { path: "/predict", label: "Delay Prediction", icon: TrainFront },
  { path: "/stations", label: "Station Insights", icon: Search },
  { path: "/model", label: "Model Insights", icon: BarChart3 },
  { path: "/health", label: "System Health", icon: Server }
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <Gauge size={26} />
        <div>
          <strong>Rail Ops</strong>
          <span>Delay Control</span>
        </div>
      </div>

      <nav className="nav-list" aria-label="Main navigation">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink key={item.path} to={item.path} className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
