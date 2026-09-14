import { useEffect, useState } from 'react'
import { Carbon } from './sections/Carbon'
import { Comparison } from './sections/Comparison'
import { Explorer } from './sections/Explorer'
import { Method } from './sections/Method'
import { PatchHero } from './sections/PatchHero'
import { loadData, type Data } from './data'

export function App() {
  const [data, setData] = useState<Data | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    loadData().then(setData, (e: Error) => setError(e.message))
  }, [])

  if (error) return <main className="page"><p>Could not load the exported data ({error}). Run <code>make export</code> first.</p></main>
  if (!data) return <main className="page"><p>Loading…</p></main>
  const test = data.patches.filter((p) => p.split === 'test')
  return (
    <main className="page">
      <PatchHero summary={data.summary} patches={test} />
      <Comparison summary={data.summary} patches={test} />
      <Explorer summary={data.summary} patches={test} />
      <Carbon summary={data.summary} />
      <Method summary={data.summary} />
    </main>
  )
}
