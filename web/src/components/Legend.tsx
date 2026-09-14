// A colour legend drawn from the scale limits recorded in summary.json.
const VIRIDIS = ['#440154', '#414487', '#2a788e', '#22a884', '#7ad151', '#fde725']
const YLGN = ['#ffffe5', '#d9f0a3', '#78c679', '#238443', '#004529']

export function Legend({ kind, range, unit }: { kind: 'agb' | 'ndvi'; range: [number, number]; unit: string }) {
  const stops = kind === 'agb' ? VIRIDIS : YLGN
  return (
    <div className="legend" role="img" aria-label={`Colour scale from ${range[0]} to ${range[1]} ${unit}`}>
      <span>{range[0]}</span>
      <span className="bar" style={{ background: `linear-gradient(to right, ${stops.join(', ')})` }} />
      <span>{range[1]}{unit && ` ${unit}`}</span>
    </div>
  )
}
