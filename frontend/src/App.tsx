import { type FormEvent, useEffect, useState } from 'react'
import './App.css'

type OrderItem = {
  id?: number
  order_id?: number
  name: string
  quantity: number
  unit_price: number
}

type Order = {
  id: number
  guest_name: string
  room_number: string
  order_type: string
  status: string
  total_amount: number
  notes?: string | null
  created_at: string
  updated_at: string
  items: OrderItem[]
}

type DeliveryTask = {
  id: number
  order_id: number
  robot_name: string
  room_tag_id?: string | null
  status: string
  room_verification_passed: boolean
  estimated_eta_minutes?: number | null
  delivered_at?: string | null
  created_at: string
  updated_at: string
}

type RobotStatus = {
  id?: number | null
  state: string
  location?: string | null
  battery_level: number
  last_updated?: string | null
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  const text = await response.text()
  if (!response.ok) {
    throw new Error(text || 'Request failed')
  }

  return text ? (JSON.parse(text) as T) : (null as T)
}

function App() {
  const [orders, setOrders] = useState<Order[]>([])
  const [deliveryTasks, setDeliveryTasks] = useState<DeliveryTask[]>([])
  const [robotStatus, setRobotStatus] = useState<RobotStatus | null>(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    guest_name: '',
    room_number: '',
    order_type: 'food',
    notes: '',
    item_name: 'Burger',
    quantity: '1',
    unit_price: '25.50',
  })

  const refreshData = async () => {
    try {
      const [orderData, taskData, robotData] = await Promise.all([
        apiFetch<Order[]>('/api/orders'),
        apiFetch<DeliveryTask[]>('/api/delivery-tasks'),
        apiFetch<RobotStatus>('/api/robot/status'),
      ])
      setOrders(orderData)
      setDeliveryTasks(taskData)
      setRobotStatus(robotData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load data')
    }
  }

  useEffect(() => {
    void refreshData()
  }, [])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    setNotice('')

    try {
      const payload = {
        guest_name: form.guest_name,
        room_number: form.room_number,
        order_type: form.order_type,
        notes: form.notes,
        items: [
          {
            name: form.item_name,
            quantity: Number(form.quantity),
            unit_price: Number(form.unit_price),
          },
        ],
      }

      const created = await apiFetch<Order>('/api/orders', {
        method: 'POST',
        body: JSON.stringify(payload),
      })

      setNotice(`Order ${created.id} created for room ${created.room_number}`)
      setForm((current) => ({ ...current, guest_name: '', room_number: '', notes: '', item_name: 'Burger', quantity: '1', unit_price: '25.50' }))
      await refreshData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create order')
    } finally {
      setLoading(false)
    }
  }

  const handleOrderAction = async (id: number, action: 'confirm' | 'prepare') => {
    try {
      await apiFetch<Order>(`/api/orders/${id}/${action}`, { method: 'POST' })
      setNotice(`Order ${id} marked ${action === 'confirm' ? 'confirmed' : 'ready for delivery'}`)
      await refreshData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Order action failed')
    }
  }

  const handleCreateTask = async (order: Order) => {
    try {
      await apiFetch<DeliveryTask>('/api/delivery-tasks', {
        method: 'POST',
        body: JSON.stringify({
          order_id: order.id,
          robot_name: 'mock-robot-01',
          room_tag_id: `tag-${order.room_number}`,
        }),
      })
      setNotice(`Delivery task created for order ${order.id}`)
      await refreshData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to queue delivery task')
    }
  }

  const orderTotal = orders.reduce((sum, order) => sum + order.total_amount, 0)

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Hotel operations</p>
          <h1>Hotel Service Dashboard</h1>
        </div>
        <div className="status-chip">
          <span className="dot" />
          {robotStatus ? robotStatus.state : 'offline'}
        </div>
      </header>

      <section className="stats-grid">
        <article className="stat-card">
          <p>Orders</p>
          <strong>{orders.length}</strong>
        </article>
        <article className="stat-card">
          <p>Ready</p>
          <strong>{orders.filter((order) => order.status === 'ready').length}</strong>
        </article>
        <article className="stat-card">
          <p>Tasks</p>
          <strong>{deliveryTasks.length}</strong>
        </article>
        <article className="stat-card accent">
          <p>Gross</p>
          <strong>${orderTotal.toFixed(2)}</strong>
        </article>
      </section>

      {error ? <div className="message error">{error}</div> : null}
      {notice ? <div className="message success">{notice}</div> : null}

      <main className="main-grid">
        <section className="panel">
          <h2>Place a guest order</h2>
          <form onSubmit={handleSubmit} className="order-form">
            <label>
              Guest name
              <input value={form.guest_name} onChange={(event) => setForm({ ...form, guest_name: event.target.value })} required />
            </label>
            <label>
              Room number
              <input value={form.room_number} onChange={(event) => setForm({ ...form, room_number: event.target.value })} required />
            </label>
            <label>
              Order type
              <select value={form.order_type} onChange={(event) => setForm({ ...form, order_type: event.target.value })}>
                <option value="food">Food</option>
                <option value="amenity">Amenity</option>
              </select>
            </label>
            <label>
              Item name
              <input value={form.item_name} onChange={(event) => setForm({ ...form, item_name: event.target.value })} required />
            </label>
            <div className="inline-fields">
              <label>
                Quantity
                <input type="number" min="1" value={form.quantity} onChange={(event) => setForm({ ...form, quantity: event.target.value })} required />
              </label>
              <label>
                Unit price
                <input type="number" min="0" step="0.01" value={form.unit_price} onChange={(event) => setForm({ ...form, unit_price: event.target.value })} required />
              </label>
            </div>
            <label>
              Notes
              <textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} rows={3} />
            </label>
            <button type="submit" disabled={loading}>
              {loading ? 'Creating order...' : 'Create order'}
            </button>
          </form>
        </section>

        <section className="panel">
          <h2>Robot status</h2>
          {robotStatus ? (
            <div className="robot-card">
              <p><strong>State:</strong> {robotStatus.state}</p>
              <p><strong>Location:</strong> {robotStatus.location || 'dock'}</p>
              <p><strong>Battery:</strong> {robotStatus.battery_level}%</p>
            </div>
          ) : (
            <p>Robot status unavailable.</p>
          )}
        </section>
      </main>

      <section className="panel full-width">
        <h2>Orders</h2>
        {orders.length === 0 ? (
          <p>No orders yet.</p>
        ) : (
          <div className="list-grid">
            {orders.map((order) => (
              <article key={order.id} className="order-card">
                <header>
                  <div>
                    <h3>{order.guest_name}</h3>
                    <p>Room {order.room_number}</p>
                  </div>
                  <span className="pill">{order.status}</span>
                </header>
                <ul>
                  {order.items.map((item) => (
                    <li key={`${order.id}-${item.name}`}>
                      {item.name} × {item.quantity} @ ${item.unit_price.toFixed(2)}
                    </li>
                  ))}
                </ul>
                <p className="total">Total: ${order.total_amount.toFixed(2)}</p>
                <div className="card-actions">
                  {order.status === 'pending' ? <button onClick={() => void handleOrderAction(order.id, 'confirm')}>Confirm</button> : null}
                  {order.status === 'confirmed' ? <button onClick={() => void handleOrderAction(order.id, 'prepare')}>Mark ready</button> : null}
                  {order.status === 'ready' ? <button onClick={() => void handleCreateTask(order)}>Queue delivery</button> : null}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="panel full-width">
        <h2>Delivery tasks</h2>
        {deliveryTasks.length === 0 ? (
          <p>No delivery tasks are queued.</p>
        ) : (
          <div className="task-list">
            {deliveryTasks.map((task) => (
              <div key={task.id} className="task-item">
                <span>{task.robot_name}</span>
                <span>Room tag: {task.room_tag_id || 'unknown'}</span>
                <span>Status: {task.status}</span>
                <span>Verification: {task.room_verification_passed ? 'passed' : 'pending'}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default App
