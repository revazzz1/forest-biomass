import { fmt, type Summary } from '../data'

export function Method({ summary }: { summary: Summary }) {
  const d = summary.dataset
  return (
    <section aria-labelledby="method">
      <h2 id="method">Method and limits</h2>
      <p>
        The data is BioMassters (Nascetti et al., 2023): 256 × 256 pixel Sentinel-2 chips of Finnish forest at 10 m, each with a
        biomass map derived from Finnish Forest Centre airborne LiDAR calibrated with field plots. This prototype uses {d.n_chips} chips,
        one cloud-free June–August image each, split by chip into {d.splits.train} for training, {d.splits.val} for validation and{' '}
        {d.splits.test} for the test set shown here. Images are block-averaged to {d.patch_size} × {d.patch_size} and the label is the
        patch mean, so the task is one number per patch, not a pixel map.
      </p>
      <p>
        A single image is a deliberate simplification: the benchmark offers twelve months and radar, and both help. LiDAR is the
        reference, not the truth; it has its own model error. Optical reflectance saturates once the canopy closes, so all three models
        flatten out above roughly 150 t/ha, which the residual chart shows. Chip coordinates are not published, so patches are browsed as
        a gallery rather than on a map.
      </p>
      <p>
        Why it matters: Finland reports forest carbon under the EU's land-use, land-use-change and forestry rules, and the forest sink has
        recently turned into a source in those accounts, so cheap and frequent biomass estimates are in demand. The EU's carbon-removal
        certification framework will need the same kind of estimate at the scale of a single stand, with an honest error bar; the{' '}
        {fmt(Math.min(...Object.values(summary.models).map((m) => m.test.rmse_tco2_per_patch)))} tCO₂ per patch reached here is that bar.
      </p>
    </section>
  )
}
