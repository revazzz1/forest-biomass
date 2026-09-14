import { useState } from 'react'
import { fmt, tco2, type Summary } from '../data'

export function Carbon({ summary }: { summary: Summary }) {
  const [agb, setAgb] = useState(Math.round(summary.dataset.agb_mean))
  const [params, setParams] = useState(summary.carbon)
  const set = (k: keyof typeof params) => (e: React.ChangeEvent<HTMLInputElement>) => setParams({ ...params, [k]: Number(e.target.value) })
  return (
    <section aria-labelledby="carbon">
      <h2 id="carbon">From biomass to carbon</h2>
      <p>
        Stored CO₂ is biomass × (1 + root-to-shoot ratio) × carbon fraction × 44⁄12 × area. The defaults below are the ones
        used everywhere on this page: above-ground biomass only, the IPCC carbon fraction of dry wood, and a 2.56 km square.
      </p>
      <div className="carbon">
        <label>Mean biomass, t/ha<input type="number" min={0} step={1} value={agb} onChange={(e) => setAgb(Number(e.target.value))} /></label>
        <label>Carbon fraction<input type="number" min={0} max={1} step={0.01} value={params.carbon_fraction} onChange={set('carbon_fraction')} /></label>
        <label>Root-to-shoot ratio<input type="number" min={0} max={2} step={0.05} value={params.root_to_shoot} onChange={set('root_to_shoot')} /></label>
        <label>Patch area, ha<input type="number" min={0} step={1} value={params.area_ha} onChange={set('area_ha')} /></label>
      </div>
      <p className="result" aria-live="polite">{fmt(tco2(agb, params))} tonnes of CO₂</p>
      <p className="small">
        Set the root-to-shoot ratio to about 0.25 to include roots, as Finnish greenhouse-gas inventories do for conifers; leave it
        at zero to match the LiDAR reference, which measures above-ground biomass only.
      </p>
    </section>
  )
}
