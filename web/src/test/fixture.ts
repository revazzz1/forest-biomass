import type { Data } from '../data'

const metrics = (rmse: number) => ({ mae: rmse * 0.8, rmse, r2: 0.5, rmse_tco2_per_patch: rmse * 1129.5, mae_tco2_per_patch: rmse * 900 })
const bins = { '0–50': { n: 3, mean_residual: 2, mae: 5 }, '50–100': { n: 4, mean_residual: -1, mae: 6 }, '100–150': { n: 2, mean_residual: -8, mae: 9 }, '150+': { n: 1, mean_residual: -20, mae: 20 } }
const model = (label: string, rmse: number) => ({ label, test: metrics(rmse), residuals_by_bin: bins, settings: {} })

export const fixture: Data = {
  summary: {
    dataset: { n_chips: 3, patch_size: 64, splits: { train: 1, val: 1, test: 2 }, exported: { test: 2, train: 1 }, agb_mean: 60, agb_max: 120 },
    models: { ridge: model('Ridge', 14), rf: model('Random forest', 16), cnn: model('CNN', 12) },
    scales: { ndvi: [0, 0.9], agb: [0, 250], rgb: [0.004, 0.09] },
    carbon: { carbon_fraction: 0.47, area_ha: 655.36, root_to_shoot: 0, co2_per_c: 44 / 12 },
  },
  patches: [
    { id: 'aaaa1111', split: 'test', agb_true: 87, ndvi: 0.71, tco2_true: 98266, pred: { ridge: 80, rf: 78, cnn: 74 }, tco2_pred: { ridge: 90360, rf: 88101, cnn: 83583 } },
    { id: 'bbbb2222', split: 'test', agb_true: 120, ndvi: 0.8, tco2_true: 135540, pred: { ridge: 100, rf: 105, cnn: 110 }, tco2_pred: { ridge: 112950, rf: 118597, cnn: 124245 } },
    { id: 'cccc3333', split: 'train', agb_true: 30, ndvi: 0.5, tco2_true: 33885, pred: { ridge: 32, rf: 31, cnn: 29 }, tco2_pred: { ridge: 36144, rf: 35014, cnn: 32755 } },
  ],
}
