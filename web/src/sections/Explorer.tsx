import { useEffect, useRef, useState } from 'react'
import { PatchImage } from '../components/PatchImage'
import { fmt, modelKeys, type ModelKey, type Patch, type Summary } from '../data'

type Sort = 'agb' | 'cnn_error' | 'ndvi'
const SORTS: Record<Sort, { label: string; key: (p: Patch) => number }> = {
  agb: { label: 'true biomass', key: (p) => -p.agb_true },
  cnn_error: { label: 'CNN error', key: (p) => -Math.abs(p.pred.cnn - p.agb_true) },
  ndvi: { label: 'NDVI', key: (p) => -p.ndvi },
}

export function Explorer({ summary, patches }: { summary: Summary; patches: Patch[] }) {
  const [sort, setSort] = useState<Sort>('agb')
  const [open, setOpen] = useState<Patch | null>(null)
  const sorts = (Object.keys(SORTS) as Sort[]).filter((s) => s !== 'cnn_error' || 'cnn' in summary.models)
  const sorted = [...patches].sort((a, b) => SORTS[sort].key(a) - SORTS[sort].key(b))
  return (
    <section aria-labelledby="explore">
      <h2 id="explore">Patch explorer</h2>
      <div className="toolbar">
        <label>
          Sort by{' '}
          <select value={sort} onChange={(e) => setSort(e.target.value as Sort)}>
            {sorts.map((s) => <option key={s} value={s}>{SORTS[s].label}</option>)}
          </select>
        </label>
        <span className="small">{patches.length} test patches, highest first</span>
      </div>
      <ul className="gallery">
        {sorted.map((p) => (
          <li key={p.id}>
            <button type="button" onClick={() => setOpen(p)} aria-label={`Open patch ${p.id}, ${fmt(p.agb_true)} t/ha`}>
              <figure>
                <PatchImage patch={p} kind="rgb" />
                <figcaption><span>{fmt(p.agb_true)} t/ha</span><span>{p.id}</span></figcaption>
              </figure>
            </button>
          </li>
        ))}
      </ul>
      <Detail summary={summary} patch={open} onClose={() => setOpen(null)} />
    </section>
  )
}

function Detail({ summary, patch, onClose }: { summary: Summary; patch: Patch | null; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (patch && !d.open) d.showModal()
    if (!patch && d.open) d.close()
  }, [patch])
  if (!patch) return <dialog ref={ref} onClose={onClose} />
  const keys = modelKeys(summary)
  return (
    <dialog ref={ref} onClose={onClose} aria-labelledby="detail-title">
      <div className="detail">
        <header>
          <h3 id="detail-title">Patch {patch.id}</h3>
          <button type="button" onClick={onClose}>Close</button>
        </header>
        <div className="triplet">
          <figure><PatchImage patch={patch} kind="rgb" /><figcaption>True colour</figcaption></figure>
          <figure><PatchImage patch={patch} kind="ndvi" /><figcaption>NDVI, mean {patch.ndvi.toFixed(2)}</figcaption></figure>
          <figure><PatchImage patch={patch} kind="agb" /><figcaption>LiDAR biomass, mean {fmt(patch.agb_true)} t/ha</figcaption></figure>
        </div>
        <PredictionScale summary={summary} patch={patch} keys={keys} />
        <table className="co2">
          <thead><tr><th>Stored CO₂, above-ground</th><th className="num">tonnes per patch</th><th>Model RMSE as a band</th></tr></thead>
          <tbody>
            <tr><td>LiDAR reference</td><td className="num">{fmt(patch.tco2_true)}</td><td /></tr>
            {keys.map((k) => <Co2Row key={k} label={summary.models[k].label} value={patch.tco2_pred[k]} rmse={summary.models[k].test.rmse_tco2_per_patch} truth={patch.tco2_true} />)}
          </tbody>
        </table>
      </div>
    </dialog>
  )
}

function Co2Row({ label, value, rmse, truth }: { label: string; value: number; rmse: number; truth: number }) {
  const max = Math.max(value + rmse, truth) * 1.1
  const pct = (v: number) => `${(100 * v) / max}%`
  return (
    <tr>
      <td>{label}</td>
      <td className="num">{fmt(value)} ± {fmt(rmse)}</td>
      <td>
        <span className="track" aria-hidden="true">
          <span className="band" style={{ left: pct(Math.max(0, value - rmse)), width: pct(Math.min(value + rmse, max) - Math.max(0, value - rmse)) }} />
          <i style={{ left: pct(truth), background: '#c9a66b' }} />
          <i style={{ left: pct(value) }} />
        </span>
      </td>
    </tr>
  )
}

function PredictionScale({ summary, patch, keys }: { summary: Summary; patch: Patch; keys: ModelKey[] }) {
  const max = Math.ceil(Math.max(summary.dataset.agb_max, patch.agb_true, ...keys.map((k) => patch.pred[k])) / 50) * 50
  const x = (v: number) => 20 + (v / max) * 760
  const colour: Record<ModelKey, string> = { ridge: '#7fa86f', rf: '#2f5d3a', cnn: '#1f3d34' }
  const byValue = [...keys].sort((a, b) => patch.pred[a] - patch.pred[b])  // one label row per model, in value order, so labels never overlap
  return (
    <svg className="scale" viewBox="0 0 800 130" role="img" aria-label={`Predictions against the LiDAR value of ${fmt(patch.agb_true)} t/ha`}>
      <line x1={20} x2={780} y1={50} y2={50} stroke="#d5dbd8" strokeWidth={2} />
      {Array.from({ length: max / 50 + 1 }, (_, i) => i * 50).map((v) => (
        <g key={v}><line x1={x(v)} x2={x(v)} y1={46} y2={54} stroke="#d5dbd8" /><text className="tick" x={x(v)} y={70} textAnchor="middle">{v}</text></g>
      ))}
      <text className="tick" x={780} y={128} textAnchor="end">t/ha</text>
      <line x1={x(patch.agb_true)} x2={x(patch.agb_true)} y1={34} y2={66} stroke="#c9a66b" strokeWidth={3} />
      <text x={x(patch.agb_true)} y={26} textAnchor="middle">LiDAR {fmt(patch.agb_true)}</text>
      {byValue.map((k, i) => (
        <g key={k}>
          <circle cx={x(patch.pred[k])} cy={50} r={6} fill={colour[k]} />
          <text x={x(patch.pred[k])} y={90 + 18 * i} textAnchor="middle" fontSize={12}>{summary.models[k].label} {fmt(patch.pred[k])}</text>
        </g>
      ))}
    </svg>
  )
}
