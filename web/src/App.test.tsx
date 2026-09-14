import { render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import { App } from './App'
import { fixture } from './test/fixture'

afterEach(() => vi.unstubAllGlobals())

test('renders the first test patch from patches.json', async () => {
  vi.stubGlobal('fetch', (url: string) => {
    const body = url.endsWith('summary.json') ? fixture.summary : fixture.patches
    return Promise.resolve({ ok: true, json: () => Promise.resolve(body) })
  })
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'Forest biomass from orbit' })).toBeInTheDocument()
  expect(screen.getAllByAltText('True-colour Sentinel-2 image of patch aaaa1111')).toHaveLength(2)
  expect(screen.getByText(/the LiDAR survey measured/)).toHaveTextContent('87 t/ha')
  expect(screen.getByRole('button', { name: 'Open patch aaaa1111, 87 t/ha' })).toBeInTheDocument()
  expect(screen.queryByAltText(/patch cccc3333/)).not.toBeInTheDocument()
})
