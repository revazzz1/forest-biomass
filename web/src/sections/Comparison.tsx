import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'
import { fmt, modelKeys, type ModelKey, type Patch, type Summary } from '../data'

const SERIES: Record<ModelKey, string> = { ridge: '#7fa86f', rf: '#2f5d3a', cnn: '#1f3d34' }

export function Comparison({ summary, patches }: { summary: Summary; patches: Patch[] }) {
  const keys = modelKeys(summary)
  const [model, setModel] = useState<ModelKey>(keys[keys.length - 1])
  const max = Math.ceil(Math.max(...patches.flatMap((p) => [p.agb_true, ...keys.map((k) => p.pred[k])])) / 50) * 50
  const ticks = Array.from({ length: max / 50 + 1 }, (_, i) => i * 50)
  const points = patches.map((p) => ({ id: p.id, x: p.agb_true, y: p.pred[model] }))
  const bins = Object.keys(summary.models[model].residuals_by_bin).map((bin) => ({
    bin,
    ...Object.fromEntries(keys.map((k) => [k, summary.models[k].residuals_by_bin[bin].mean_residual])),
  }))
  return (
    <section aria-labelledby="compare">
      <h2 id="compare">How well can a satellite image guess the forest?</h2>
      <div className="toggle" role="group" aria-label="Model">
        {keys.map((k) => (
          <button key={k} type="button" aria-pressed={model === k} onClick={() => setModel(k)}>{summary.models[k].label}</button>
        ))}
      </div>
      <div className="compare">
        <div>
          <div className="chart">
            <ResponsiveContainer>
              <ScatterChart margin={{ top: 8, right: 16, bottom: 24, left: 16 }}>
                <CartesianGrid stroke="#d5dbd8" />
                <XAxis type="number" dataKey="x" domain={[0, max]} ticks={ticks} name="LiDAR biomass" label={{ value: 'LiDAR biomass (t/ha)', position: 'bottom', offset: 8 }} />
                <YAxis type="number" dataKey="y" domain={[0, max]} ticks={ticks} name="Predicted" width={60} label={{ value: 'Predicted (t/ha)', angle: -90, position: 'insideLeft', offset: 8 }} />
                <ReferenceLine segment={[{ x: 0, y: 0 }, { x: max, y: max }]} stroke="#4b5350" strokeDasharray="4 4" />
                <Tooltip formatter={(v) => `${fmt(Number(v), 1)} t/ha`} labelFormatter={() => ''} />
                <Scatter data={points} fill={SERIES[model]} fillOpacity={0.75} isAnimationActive={false} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <p className="small">Each dot is one test patch: what the LiDAR measured against what the {summary.models[model].label} predicted. The dashed line is a perfect guess.</p>
        </div>
        <table>
          <thead>
            <tr><th>Model</th><th className="num">MAE</th><th className="num">RMSE</th><th className="num">R²</th><th className="num">RMSE as tCO₂ per patch</th></tr>
          </thead>
          <tbody>
            {keys.map((k) => (
              <tr key={k} className={k === model ? 'active' : ''}>
                <td>{summary.models[k].label}</td>
                <td className="num">{fmt(summary.models[k].test.mae, 1)}</td>
                <td className="num">{fmt(summary.models[k].test.rmse, 1)}</td>
                <td className="num">{fmt(summary.models[k].test.r2, 2)}</td>
                <td className="num">{fmt(summary.models[k].test.rmse_tco2_per_patch)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3 style={{ marginTop: '2rem' }}>Where the models miss</h3>
      <div className="chart short">
        <ResponsiveContainer>
          <BarChart data={bins} margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
            <CartesianGrid stroke="#d5dbd8" vertical={false} />
            <XAxis dataKey="bin" label={{ value: 'LiDAR biomass (t/ha)', position: 'bottom', offset: 8 }} />
            <YAxis width={60} tickFormatter={(v) => fmt(Number(v))} label={{ value: 'Mean residual (t/ha)', angle: -90, position: 'insideLeft', offset: 8 }} />
            <ReferenceLine y={0} stroke="#4b5350" />
            <Tooltip formatter={(v, name) => [`${fmt(Number(v), 1)} t/ha`, summary.models[name as ModelKey].label]} />
            {keys.map((k) => <Bar key={k} dataKey={k} fill={SERIES[k]} fillOpacity={k === model ? 1 : 0.45} isAnimationActive={false} />)}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="small">
        Mean of prediction minus truth, by true biomass. Optical reflectance stops changing once the canopy closes, so every model
        under-predicts the densest stands: the bars go negative at high biomass.
      </p>
    </section>
  )
}
