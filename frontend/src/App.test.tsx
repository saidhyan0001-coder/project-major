import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'

const menu = [
  { id: 1, name: 'Garden salad', category: 'Mains', description: 'Fresh greens', unit_price: 13, available: true },
]

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/v1/menu')) {
      return new Response(JSON.stringify(menu), { status: 200 })
    }
    if (url.endsWith('/api/v1/orders/preview')) {
      return new Response(JSON.stringify({ total_amount: 13 }), { status: 200 })
    }
    if (url.endsWith('/api/v1/orders') && init?.method === 'POST') {
      return new Response(JSON.stringify({
        id: 42, status: 'pending', total_amount: 13, tracking_token: 'a'.repeat(64),
        guest_name: 'Taylor Guest', room_number: '501',
        items: [{ name: 'Garden salad', quantity: 1, unit_price: 13 }],
      }), { status: 201 })
    }
    if (url.endsWith('/api/v1/orders/42/confirm')) {
      return new Response(JSON.stringify({
        id: 42, status: 'confirmed', total_amount: 13, guest_name: 'Taylor Guest',
        room_number: '501', items: [{ name: 'Garden salad', quantity: 1, unit_price: 13 }],
      }), { status: 200 })
    }
    return new Response('Not found', { status: 404 })
  }))
})

afterEach(() => vi.unstubAllGlobals())

test('shows menu and only reports an order after backend confirmation', async () => {
  const user = userEvent.setup()
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'Garden salad' })).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: /add to order/i }))
  await user.type(screen.getByLabelText(/your name/i), 'Taylor Guest')
  await user.type(screen.getByLabelText(/room number/i), '501')
  await user.click(screen.getByRole('button', { name: /review & confirm order/i }))
  await waitFor(() => expect(screen.getByText(/order #42 confirmed/i)).toBeInTheDocument())
})

test('allows entering guest details after creating an assistant order draft', async () => {
  const user = userEvent.setup()
  const fetchMock = vi.mocked(fetch)
  fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/v1/menu')) return new Response(JSON.stringify(menu), { status: 200 })
    if (url.endsWith('/api/v1/conversations')) {
      return new Response(JSON.stringify({ session_id: 'session-1' }), { status: 200 })
    }
    if (url.endsWith('/api/v1/conversations/session-1/messages')) {
      return new Response(JSON.stringify({
        session_id: 'session-1',
        response: 'I have prepared a draft.',
        intent: 'order',
        proposed_items: [{ menu_item_id: 1, name: 'Garden salad', quantity: 1, unit_price: 13 }],
      }), { status: 200 })
    }
    if (url.endsWith('/api/v1/conversations/session-1/confirm')) {
      const payload = JSON.parse(String(init?.body))
      expect(payload).toEqual({ text: 'confirm', guest_name: 'Taylor Guest', room_number: '501' })
      return new Response(JSON.stringify({
        id: 43, status: 'confirmed', total_amount: 13, tracking_token: 'b'.repeat(64),
        guest_name: 'Taylor Guest', room_number: '501',
        items: [{ name: 'Garden salad', quantity: 1, unit_price: 13 }],
      }), { status: 201 })
    }
    return new Response('Not found', { status: 404 })
  })

  render(<App />)
  await user.type(screen.getByRole('textbox', { name: 'Message the voice assistant' }), 'Garden salad')
  await user.click(screen.getByRole('button', { name: 'Send message' }))
  await screen.findByText('Order draft (not yet placed)')
  await user.type(screen.getByLabelText(/your name/i), 'Taylor Guest')
  await user.type(screen.getByLabelText(/room number/i), '501')
  await user.click(screen.getByRole('button', { name: 'Confirm this order' }))
  await waitFor(() => expect(screen.getByRole('heading', { name: /order #43 confirmed/i })).toBeInTheDocument())
})
