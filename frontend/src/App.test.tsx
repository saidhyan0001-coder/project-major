import { render, screen, waitFor } from '@testing-library/react'
import App from './App'

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.includes('/api/robot/status')) {
      return {
        ok: true,
        text: async () => JSON.stringify({ state: 'idle', location: 'dock', battery_level: 100 }),
      }
    }

    return {
      ok: true,
      text: async () => JSON.stringify([
        {
          id: 1,
          guest_name: 'Jane Guest',
          room_number: '304',
          order_type: 'food',
          status: 'ready',
          total_amount: 25.5,
          notes: '',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          items: [{ id: 1, order_id: 1, name: 'Burger', quantity: 1, unit_price: 25.5 }],
        },
      ]),
    }
  }))
})

afterEach(() => {
  vi.unstubAllGlobals()
})

test('renders the hotel delivery dashboard', async () => {
  render(<App />)

  await waitFor(() => {
    expect(screen.getByRole('heading', { name: /hotel service dashboard/i })).toBeInTheDocument()
  })
  expect(screen.getAllByText(/orders/i).length).toBeGreaterThan(0)
})
