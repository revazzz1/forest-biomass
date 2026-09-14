// Types for web/public/data, written by `make export`. Every number on the page comes from here.
export type ModelKey = 'ridge' | 'rf' | 'cnn'
export const MODEL_KEYS: ModelKey[] = ['ridge', 'rf', 'cnn']

export interface Metrics {
  mae: number
  rmse: number
  r2: number
  rmse_tco2_per_patch: number
  mae_tco2_per_patch: number
}
export interface ModelSummary {
  label: string
  test: Metrics
  residuals_by_bin: Record<string, { n: number; mean_residual: number; mae: number }>
  settings: Record<string, unknown>
}
export interface Carbon {
  carbon_fraction: number
  area_ha: number
  root_to_shoot: number
  co2_per_c: number
}
export interface Summary {
  dataset: {
    n_chips: number
    patch_size: number
    splits: Record<string, number>
    exported: Record<string, number>
    agb_mean: number
    agb_max: number
  }
  models: Record<ModelKey, ModelSummary>
  scales: { ndvi: [number, number]; agb: [number, number]; rgb: [number, number] }
  carbon: Carbon
}
export interface Patch {
  id: string
  split: 'test' | 'train'
  agb_true: number
  ndvi: number
  tco2_true: number
  pred: Record<ModelKey, number>
  tco2_pred: Record<ModelKey, number>
}
export interface Data {
  summary: Summary
  patches: Patch[]
}

const base = `${import.meta.env.BASE_URL}data/`
export const imageUrl = (id: string, kind: 'rgb' | 'ndvi' | 'agb') => `${base}patches/${id}_${kind}.png`

export async function loadData(): Promise<Data> {
  const get = (name: string) => fetch(base + name).then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${name}: ${r.status}`))))
  const [summary, patches] = await Promise.all([get('summary.json'), get('patches.json')])
  return { summary, patches }
}

// Same formula as biomass/carbon.py: agb × (1 + root:shoot) × carbon fraction × 44/12 × area.
export const tco2 = (agb: number, c: Carbon) => agb * (1 + c.root_to_shoot) * c.carbon_fraction * c.co2_per_c * c.area_ha

export const fmt = (n: number, digits = 0) =>
  n.toLocaleString('en-GB', { maximumFractionDigits: digits, minimumFractionDigits: digits })

export const modelKeys = (s: Summary) => MODEL_KEYS.filter((k) => k in s.models)
