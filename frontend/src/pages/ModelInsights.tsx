import { PageHeader } from "../components/PageHeader";
import { ZoneChart } from "../components/ZoneChart";
import { getModelInfo } from "../services/api";
import { useApi } from "../hooks/useApi";

function featureLabel(feature: string) {
  return feature.replace(/_/g, " ");
}

export function ModelInsights() {
  const { data } = useApi(getModelInfo, []);
  const features = data?.feature_importance ?? [];

  return (
    <section className="page">
      <PageHeader eyebrow="Model Registry" title="Model Insights" />
      <div className="model-summary ops-panel">
        <div>
          <span>Active Model</span>
          <strong>{data?.model_name ?? "--"}</strong>
        </div>
        <div>
          <span>Version</span>
          <strong>{data?.model_version ?? "--"}</strong>
        </div>
        <div>
          <span>MAE</span>
          <strong>{data?.metrics.mae ?? "--"}</strong>
        </div>
        <div>
          <span>RMSE</span>
          <strong>{data?.metrics.rmse ?? "--"}</strong>
        </div>
      </div>

      <div className="two-column">
        <section className="ops-panel">
          <div className="section-heading">
            <h2>Feature Importance</h2>
            <span>SHAP-ready model signal ranking</span>
          </div>
          <ZoneChart
            data={features.map((item) => ({ train_type: featureLabel(item.feature), average_delay: item.importance, records: 0 }))}
            dataKey="train_type"
          />
        </section>
        <section className="ops-panel">
          <div className="section-heading">
            <h2>Top Influencing Features</h2>
            <span>Plain English explanations</span>
          </div>
          <div className="explanation-list">
            {features.slice(0, 6).map((feature) => (
              <p key={feature.feature}>
                <strong>{featureLabel(feature.feature)}</strong>
                {` contributes approximately ${Math.round(feature.importance * 100)}% of prediction variance.`}
              </p>
            ))}
          </div>
        </section>
      </div>
    </section>
  );
}
