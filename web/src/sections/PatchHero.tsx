import { useState } from 'react'
import { Legend } from '../components/Legend'
import { PatchImage } from '../components/PatchImage'
import { fmt, modelKeys, type Patch, type Summary } from '../data'

export function PatchHero({ summary, patches }: { summary: Summary; patches: Patch[] }) {
  const [index, setIndex] = useState(0)
  const [previous, setPrevious] = useState<Patch | null>(null)
  const [loaded, setLoaded] = useState<Record<string, boolean>>({})
  const patch = patches[index]
  const keys = modelKeys(summary)
  const best = keys.reduce((a, b) => (summary.models[a].test.rmse <= summary.models[b].test.rmse ? a : b))
  const gap = patch.pred[best] - patch.agb_true
  const step = (d: number) => {
    setPrevious(patch)
    setIndex((i) => (i + d + patches.length) % patches.length)
  }
  const frame = (kind: 'rgb' | 'agb') => (
    <figure>
      <div className="frame">
        {previous && previous.id !== patch.id && <PatchImage patch={previous} kind={kind} />}
        <PatchImage key={patch.id} patch={patch} kind={kind} className={loaded[`${patch.id}_${kind}`] ? 'in' : 'pending'}
                    onLoad={() => setLoaded((l) => ({ ...l, [`${patch.id}_${kind}`]: true }))} />
      </div>
      <figcaption>{kind === 'rgb' ? 'Sentinel-2, true colour, one summer image' : 'Airborne LiDAR biomass, the reference'}</figcaption>
      {kind === 'agb' && <Legend kind="agb" range={summary.scales.agb} unit="t/ha" />}
    </figure>
  )
  return (
    <section aria-labelledby="title">
      <h1 id="title">Forest biomass from orbit</h1>
      <p className="lede">
        Can one summer satellite image tell how much wood, and so how much carbon, stands in 2.56 km of Finnish forest?
        Three models tried on {summary.dataset.n_chips} patches. These are the {patches.length} patches none of them saw during training.
      </p>
      <div className="hero-pair">{frame('rgb')}{frame('agb')}</div>
      <p className="headline">
        On patch {patch.id} the LiDAR survey measured <strong>{fmt(patch.agb_true)} t/ha</strong>.{' '}
        {keys.map((k, i) => (
          <span key={k}>{i > 0 && (i === keys.length - 1 ? ' and ' : ', ')}{summary.models[k].label} guessed <strong>{fmt(patch.pred[k])}</strong></span>
        ))}
        . The {summary.models[best].label}'s miss of {fmt(Math.abs(gap))} t/ha is{' '}
        <strong>{fmt(Math.abs(patch.tco2_pred[best] - patch.tco2_true))} tonnes of CO₂</strong> on this {fmt(summary.carbon.area_ha)} ha patch,
        above-ground biomass only.
      </p>
      <div className="stepper">
        <button type="button" onClick={() => step(-1)} aria-label="Previous patch">Previous</button>
        <button type="button" onClick={() => step(1)} aria-label="Next patch">Next</button>
        <span>{index + 1} of {patches.length}</span>
      </div>
    </section>
  )
}
