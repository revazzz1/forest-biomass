import { imageUrl, fmt, type Patch } from '../data'

export const altText = (p: Patch, kind: 'rgb' | 'ndvi' | 'agb') =>
  ({
    rgb: `True-colour Sentinel-2 image of patch ${p.id}`,
    ndvi: `NDVI map of patch ${p.id}, mean ${p.ndvi.toFixed(2)}`,
    agb: `Airborne LiDAR biomass map of patch ${p.id}, mean ${fmt(p.agb_true)} t/ha`,
  })[kind]

export function PatchImage({ patch, kind, className }: { patch: Patch; kind: 'rgb' | 'ndvi' | 'agb'; className?: string }) {
  return <img src={imageUrl(patch.id, kind)} alt={altText(patch, kind)} width={256} height={256} className={className} />
}
