import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { DelayPrediction } from "./pages/DelayPrediction";
import { ModelInsights } from "./pages/ModelInsights";
import { Overview } from "./pages/Overview";
import { StationInsights } from "./pages/StationInsights";
import { SystemHealth } from "./pages/SystemHealth";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/overview" replace />} />
        <Route path="/overview" element={<Overview />} />
        <Route path="/predict" element={<DelayPrediction />} />
        <Route path="/stations" element={<StationInsights />} />
        <Route path="/model" element={<ModelInsights />} />
        <Route path="/health" element={<SystemHealth />} />
      </Routes>
    </Layout>
  );
}
