import { Activity, Database, ServerCog, ShieldCheck } from "lucide-react";

import { InfoStrip } from "../components/InfoStrip";
import { PageHeader } from "../components/PageHeader";
import { getHealth, getModelInfo } from "../services/api";
import { useApi } from "../hooks/useApi";

export function SystemHealth() {
  const health = useApi(getHealth, []);
  const model = useApi(getModelInfo, []);

  return (
    <section className="page">
      <PageHeader eyebrow="Monitoring" title="System Health" />
      <div className="strip-grid">
        <InfoStrip label="API Status" value={health.data?.api_status ?? "--"} icon={Activity} tone="good" />
        <InfoStrip label="Model Version" value={model.data?.model_version ?? "--"} icon={ServerCog} />
        <InfoStrip label="Dataset Size" value={health.data?.dataset_size ?? "--"} icon={Database} />
        <InfoStrip label="Environment" value={health.data?.environment ?? "--"} icon={ShieldCheck} />
      </div>

      <section className="ops-panel health-grid">
        <div>
          <span>Model Status</span>
          <strong>{health.data?.model_status ?? "--"}</strong>
        </div>
        <div>
          <span>Training Date</span>
          <strong>{model.data?.trained_at ? new Date(model.data.trained_at).toLocaleString() : "Not trained"}</strong>
        </div>
        <div>
          <span>MAE</span>
          <strong>{model.data?.metrics.mae ?? "--"}</strong>
        </div>
        <div>
          <span>RMSE</span>
          <strong>{model.data?.metrics.rmse ?? "--"}</strong>
        </div>
        <div>
          <span>R2</span>
          <strong>{model.data?.metrics.r2 ?? "--"}</strong>
        </div>
      </section>
    </section>
  );
}
