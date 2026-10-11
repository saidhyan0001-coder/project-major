import { type FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import './App.css'

type MenuItem = { id: number; name: string; category: string; description: string; unit_price: number; available: boolean }
type CreatedOrder = {
  id: number
  status: string
  total_amount: number
  tracking_token: string
  guest_name: string
  room_number: string
  items: Array<{ name: string; quantity: number; unit_price: number }>
}
type ChatMessage = { role: 'guest' | 'assistant'; text: string }
type ProposedItem = { menu_item_id: number; name: string; quantity: number; unit_price: number }
type AprilTagEvent = { id: number; room_number: string; floor_id: string; observed_family: string; observed_tag_id: number; decision_margin: number; result: string; created_at: string }
type BrowserRecognition = {
  lang: string
  continuous: boolean
  interimResults: boolean
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null
  onerror: ((event: { error: string }) => void) | null
  onend: (() => void) | null
  start(): void
  stop(): void
}
type BrowserRecognitionConstructor = new () => BrowserRecognition

const API_BASE = import.meta.env.VITE_API_BASE_URL
  || (import.meta.env.DEV ? 'http://localhost:8000' : window.location.origin)

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    })
  } catch {
    throw new Error('Unable to reach the hotel service. Check your connection and try again.')
  }
  const body = await response.text()
  if (!response.ok) {
    let detail = body || `Request failed (${response.status})`
    try {
      detail = JSON.parse(body).detail || detail
    } catch {
      // Keep the response text for non-JSON upstream errors.
    }
    throw new Error(detail)
  }
  return body ? JSON.parse(body) as T : null as T
}

function App() {
  const [menu, setMenu] = useState<MenuItem[]>([])
  const [cart, setCart] = useState<Record<number, number>>({})
  const [guestName, setGuestName] = useState('')
  const [roomNumber, setRoomNumber] = useState('')
  const [notes, setNotes] = useState('')
  const [order, setOrder] = useState<CreatedOrder | null>(null)
  const [tracked, setTracked] = useState<CreatedOrder | null>(null)
  const [trackingId, setTrackingId] = useState('')
  const [trackingToken, setTrackingToken] = useState('')
  const [chatText, setChatText] = useState('')
  const [chat, setChat] = useState<ChatMessage[]>([])
  const [sessionId, setSessionId] = useState('')
  const [draft, setDraft] = useState<ProposedItem[]>([])
  const [staffToken, setStaffToken] = useState('')
  const [staffOrders, setStaffOrders] = useState<Array<{ id: number; guest_name: string; room_number: string; status: string; total_amount: number }>>([])
  const [apriltagEvents, setApriltagEvents] = useState<AprilTagEvent[]>([])
  const [tagMapping, setTagMapping] = useState({ room_number: '', floor_id: '', tag_family: 'tag36h11', tag_id: '' })
  const [staffOpen, setStaffOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [listening, setListening] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const recognitionRef = useRef<BrowserRecognition | null>(null)

  const cartLines = useMemo(
    () => menu.filter((item) => cart[item.id]).map((item) => ({ item, quantity: cart[item.id] })),
    [menu, cart],
  )
  const estimatedTotal = cartLines.reduce((sum, line) => sum + line.item.unit_price * line.quantity, 0)

  useEffect(() => {
    void api<MenuItem[]>('/api/v1/menu').then(setMenu).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : 'Could not load menu.')
    })
  }, [])

  const updateQuantity = (itemId: number, quantity: number) => {
    setCart((current) => {
      const next = { ...current }
      if (quantity <= 0) delete next[itemId]
      else next[itemId] = Math.min(quantity, 20)
      return next
    })
  }

  const sendChat = async (text = chatText) => {
    const content = text.trim()
    if (!content || loading) return
    setChatText('')
    setError('')
    setChat((messages) => [...messages, { role: 'guest', text: content }])
    setLoading(true)
    try {
      let currentSession = sessionId
      if (!currentSession) {
        const created = await api<{ session_id: string }>('/api/v1/conversations', {
          method: 'POST',
          body: JSON.stringify({ guest_name: guestName || null, room_number: roomNumber || null }),
        })
        currentSession = created.session_id
        setSessionId(currentSession)
      }
      const reply = await api<{ response: string; proposed_items: ProposedItem[]; security_flagged: boolean }>(
        `/api/v1/conversations/${currentSession}/messages`,
        { method: 'POST', body: JSON.stringify({ text: content }) },
      )
      setChat((messages) => [...messages, { role: 'assistant', text: reply.response }])
      if (reply.proposed_items.length) setDraft(reply.proposed_items)
      if (reply.security_flagged) setNotice('The message was blocked by the assistant’s safety checks.')
      if ('speechSynthesis' in window && !reply.security_flagged) {
        window.speechSynthesis.cancel()
        window.speechSynthesis.speak(new SpeechSynthesisUtterance(reply.response))
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Assistant request failed.')
    } finally {
      setLoading(false)
    }
  }

  const startVoice = () => {
    const browserWindow = window as Window & {
      SpeechRecognition?: BrowserRecognitionConstructor
      webkitSpeechRecognition?: BrowserRecognitionConstructor
    }
    const Recognition = browserWindow.SpeechRecognition || browserWindow.webkitSpeechRecognition
    if (!Recognition) {
      setError('Speech recognition is not supported by this browser. You can still type to the assistant.')
      return
    }
    setError('')
    setNotice('Microphone audio is processed by your browser speech service. Review your browser privacy settings.')
    const recognition = new Recognition()
    recognitionRef.current = recognition
    recognition.lang = 'en-US'
    recognition.continuous = false
    recognition.interimResults = false
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript
      if (transcript) void sendChat(transcript)
    }
    recognition.onerror = (event) => {
      setError(event.error === 'not-allowed'
        ? 'Microphone permission was denied. Allow microphone access in your browser or type your request.'
        : `Speech recognition error: ${event.error}. You can retry or type your request.`)
      setListening(false)
    }
    recognition.onend = () => setListening(false)
    try {
      setListening(true)
      recognition.start()
    } catch {
      setListening(false)
      setError('Could not start microphone capture. Please retry or type your request.')
    }
  }

  const stopVoice = () => {
    recognitionRef.current?.stop()
    setListening(false)
    setNotice('Microphone stopped.')
  }

  const createAndConfirm = async (event: FormEvent) => {
    event.preventDefault()
    if (!cartLines.length) {
      setError('Add at least one item before placing your order.')
      return
    }
    setLoading(true)
    setError('')
    setNotice('')
    try {
      const preview = await api<{ total_amount: number }>('/api/v1/orders/preview', {
        method: 'POST',
        body: JSON.stringify({
          guest_name: guestName,
          room_number: roomNumber,
          items: cartLines.map(({ item, quantity }) => ({ menu_item_id: item.id, quantity })),
        }),
      })
      const created = await api<CreatedOrder>('/api/v1/orders', {
        method: 'POST',
        body: JSON.stringify({
          guest_name: guestName,
          room_number: roomNumber,
          notes,
          items: cartLines.map(({ item, quantity }) => ({ menu_item_id: item.id, quantity })),
        }),
      })
      if (Math.abs(created.total_amount - preview.total_amount) > 0.001) {
        throw new Error('The server price changed while placing your order. Please review the menu and try again.')
      }
      const confirmed = await api<Omit<CreatedOrder, 'tracking_token'>>(`/api/v1/orders/${created.id}/confirm`, {
        method: 'POST',
        body: JSON.stringify({ tracking_token: created.tracking_token }),
      })
      const placed = { ...created, ...confirmed }
      setOrder(placed)
      setTracked(placed)
      setTrackingId(String(placed.id))
      setTrackingToken(created.tracking_token)
      setCart({})
      setNotice(`Order #${placed.id} is confirmed. Save your tracking details to check status later.`)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Order could not be confirmed.')
    } finally {
      setLoading(false)
    }
  }

  const trackOrder = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    try {
      const result = await api<CreatedOrder>(`/api/v1/orders/${trackingId}/track`, {
        method: 'POST',
        body: JSON.stringify({ tracking_token: trackingToken }),
      })
      setTracked(result)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not find that order.')
    }
  }

  const confirmVoiceDraft = async () => {
    if (!sessionId || !draft.length) return
    if (!guestName.trim() || !roomNumber.trim()) {
      setError('Enter your name and room number above before confirming the voice draft.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const result = await api<CreatedOrder>(`/api/v1/conversations/${sessionId}/confirm`, {
        method: 'POST',
        body: JSON.stringify({ text: 'confirm', guest_name: guestName, room_number: roomNumber }),
      })
      setOrder(result)
      setTracked(result)
      setTrackingId(String(result.id))
      setTrackingToken(result.tracking_token)
      setDraft([])
      setNotice(`Voice order #${result.id} confirmed. Keep its tracking token private.`)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not confirm the voice order.')
    } finally {
      setLoading(false)
    }
  }

  const loadStaffOrders = async () => {
    setError('')
    try {
      const result = await api<typeof staffOrders>('/api/v1/staff/orders', {
        headers: { Authorization: `Bearer ${staffToken}` },
      })
      setStaffOrders(result)
      const tagEvents = await api<AprilTagEvent[]>('/api/v1/staff/apriltag-events', {
        headers: { Authorization: `Bearer ${staffToken}` },
      })
      setApriltagEvents(tagEvents)
      setStaffOpen(true)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Staff sign in failed.')
    }
  }

  const saveTagMapping = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    try {
      await api('/api/v1/staff/apriltag-mappings', {
        method: 'PUT',
        headers: { Authorization: `Bearer ${staffToken}` },
        body: JSON.stringify({ ...tagMapping, tag_id: Number(tagMapping.tag_id) }),
      })
      setNotice(`AprilTag mapping saved for room ${tagMapping.room_number}, floor ${tagMapping.floor_id}.`)
      const events = await api<AprilTagEvent[]>('/api/v1/staff/apriltag-events', {
        headers: { Authorization: `Bearer ${staffToken}` },
      })
      setApriltagEvents(events)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not save AprilTag mapping.')
    }
  }

  const setStaffStatus = async (id: number, nextStatus: string) => {
    try {
      await api(`/api/v1/staff/orders/${id}/status`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${staffToken}` },
        body: JSON.stringify({ status: nextStatus }),
      })
      await loadStaffOrders()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not update order.')
    }
  }

  return (
    <div className="page">
      <header className="nav">
        <a className="brand" href="#home" aria-label="The Willow Hotel home">
          <span className="brand-mark">W</span>
          <span><b>THE WILLOW</b><small>HOTEL · ROOM SERVICE</small></span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#menu">Menu</a><a href="#assistant">Voice assistant</a><a href="#track">Track order</a>
        </nav>
        <a className="cart-link" href="#cart">Your order <span>{cartLines.reduce((count, line) => count + line.quantity, 0)}</span></a>
      </header>

      <main id="home">
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">A little comfort, delivered</p>
            <h1>Stay in.<br /><em>Eat beautifully.</em></h1>
            <p className="hero-text">Thoughtful dishes from our kitchen, brought to the comfort of your room.</p>
            <a className="button button-dark" href="#menu">Explore the menu <span aria-hidden="true">↗</span></a>
            <div className="hero-foot"><span>✳ FRESHLY PREPARED</span><span>✳ ORDER ANYTIME</span></div>
          </div>
          <div className="hero-photo" role="img" aria-label="An elegant hotel dining table">
            <div className="photo-caption"><span>01 / ROOM SERVICE</span><b>Made for slow mornings.</b></div>
          </div>
        </section>

        {error && <div className="alert error" role="alert">{error}<button className="text-button" onClick={() => setError('')}>Dismiss</button></div>}
        {notice && <div className="alert success" role="status">{notice}</div>}

        <section className="section menu-section" id="menu">
          <div className="section-heading">
            <div><p className="eyebrow">FROM OUR KITCHEN</p><h2>Something lovely,<br /><em>at any hour.</em></h2></div>
            <p>Seasonal favourites and familiar comforts, prepared fresh and served right to your door.</p>
          </div>
          {!menu.length ? <p className="muted">Loading today's menu…</p> : (
            <div className="menu-grid">
              {menu.map((item, index) => (
                <article className="menu-card" key={item.id}>
                  <div className={`dish-art art-${index % 5}`} aria-hidden="true"><span>{['✿', '◉', '❋', '✺', '◌'][index % 5]}</span></div>
                  <div className="menu-card-info"><div><span className="category">{item.category}</span><h3>{item.name}</h3></div><strong>${item.unit_price.toFixed(2)}</strong></div>
                  <p>{item.description}</p>
                  <button className="add-button" onClick={() => updateQuantity(item.id, (cart[item.id] || 0) + 1)}>Add to order <span>＋</span></button>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="order-section section" id="cart">
          <div className="order-intro"><p className="eyebrow">YOUR TABLE, YOUR WAY</p><h2>Your room,<br /><em>your order.</em></h2><p>We’ll bring it up warm and freshly made.</p></div>
          <form className="order-panel" onSubmit={createAndConfirm}>
            <div className="panel-top"><div><span className="step-number">01</span><h3>Review your order</h3></div><span className="secure-label">SERVER-PRICED</span></div>
            {cartLines.length === 0 ? <p className="empty-cart">Your order is waiting for something delicious.</p> : (
              <ul className="cart-list">{cartLines.map(({ item, quantity }) => (
                <li key={item.id}><div><b>{item.name}</b><small>${item.unit_price.toFixed(2)} each</small></div><div className="quantity"><button type="button" aria-label={`Remove one ${item.name}`} onClick={() => updateQuantity(item.id, quantity - 1)}>−</button><span>{quantity}</span><button type="button" aria-label={`Add one ${item.name}`} onClick={() => updateQuantity(item.id, quantity + 1)}>＋</button></div></li>
              ))}</ul>
            )}
            <div className="estimate"><span>Estimated total</span><b>${estimatedTotal.toFixed(2)}</b></div>
            <p className="fine-print">Final prices and availability are checked by the hotel server before confirmation.</p>
            <div className="form-grid">
              <label>Your name<input value={guestName} onChange={(event) => setGuestName(event.target.value)} autoComplete="name" required /></label>
              <label>Room number<input value={roomNumber} onChange={(event) => setRoomNumber(event.target.value)} autoComplete="off" required /></label>
            </div>
            <label className="notes-label">Kitchen notes <textarea value={notes} onChange={(event) => setNotes(event.target.value)} maxLength={1000} placeholder="Allergies or special requests" rows={2} /></label>
            <button className="button button-dark submit-button" disabled={loading || !cartLines.length}>{loading ? 'Checking with the kitchen…' : 'Review & confirm order'}</button>
            <p className="fine-print">Submitting places and confirms the order. You’ll receive a private tracking token.</p>
          </form>
        </section>

        <section className="assistant-section section" id="assistant">
          <div className="assistant-copy"><p className="eyebrow">A HELPFUL LITTLE VOICE</p><h2>Not sure what<br /><em>you’re craving?</em></h2><p>Ask about the menu or say what sounds good. Your assistant can suggest a draft; it will never place an order without your confirmation.</p><div className="privacy-note">Microphone access is optional. This browser uses its speech recognition service; your transcript is sent to the hotel backend for a reply. Text chat works without a microphone.</div></div>
          <div className="chat-panel">
            <div className="chat-header"><span className="assistant-avatar">W</span><div><b>Willow, your hotel host</b><small>Here to help with room service</small></div><span className="live-indicator">● READY</span></div>
            <div className="chat-messages" aria-live="polite">
              {chat.length === 0 && <div className="chat-bubble assistant-bubble">Good evening. Tell me what you’re in the mood for, or ask what’s on our menu.</div>}
              {chat.map((message, index) => <div className={`chat-bubble ${message.role === 'guest' ? 'guest-bubble' : 'assistant-bubble'}`} key={`${message.role}-${index}`}>{message.text}</div>)}
              {loading && <div className="chat-bubble assistant-bubble">One moment while I check…</div>}
            </div>
            {draft.length > 0 && <div className="draft-card"><b>Order draft (not yet placed)</b>{draft.map((item) => <div key={item.menu_item_id}>{item.quantity} × {item.name} — ${(item.quantity * item.unit_price).toFixed(2)}</div>)}<button className="button button-dark" onClick={() => void confirmVoiceDraft()} disabled={loading}>Confirm this order</button></div>}
            <form className="chat-input" onSubmit={(event) => { event.preventDefault(); void sendChat() }}>
              <button className={`mic-button ${listening ? 'is-listening' : ''}`} type="button" onClick={listening ? stopVoice : startVoice} aria-label={listening ? 'Stop voice input' : 'Start voice input'} title={listening ? 'Stop microphone' : 'Use microphone'}>{listening ? '■' : '🎙'}</button>
              <input value={chatText} onChange={(event) => setChatText(event.target.value)} placeholder="Ask about the menu…" aria-label="Message the voice assistant" />
              <button className="send-button" type="submit" disabled={loading || !chatText.trim()} aria-label="Send message">↑</button>
            </form>
            <p className="chat-consent">By using the microphone, you consent to your browser’s speech recognition processing your audio.</p>
          </div>
        </section>

        <section className="track-section section" id="track">
          <div><p className="eyebrow">ALREADY ORDERED?</p><h2>Follow the<br /><em>little details.</em></h2><p>Use the order number and private token shown at confirmation.</p></div>
          <div className="track-panel">
            {order && <div className="order-result"><span className="success-check">✓</span><h3>Order #{order.id} confirmed</h3><p>${order.total_amount.toFixed(2)} · Room {order.room_number} · {order.status}</p><label>Private tracking token<input value={order.tracking_token} readOnly onFocus={(event) => event.currentTarget.select()} /></label><small>Save this token somewhere private. It grants access to this order only.</small></div>}
            <form onSubmit={trackOrder}>
              <label>Order number<input value={trackingId} onChange={(event) => setTrackingId(event.target.value)} inputMode="numeric" required /></label>
              <label>Private tracking token<input value={trackingToken} onChange={(event) => setTrackingToken(event.target.value)} required /></label>
              <button className="button button-dark" type="submit">Check order status</button>
            </form>
            {tracked && !order && <p className="tracked-status">Order #{tracked.id}: <b>{tracked.status}</b> · ${tracked.total_amount.toFixed(2)}</p>}
          </div>
        </section>
      </main>

      <footer className="footer"><a className="brand" href="#home"><span className="brand-mark">W</span><span><b>THE WILLOW</b><small>HOTEL · ROOM SERVICE</small></span></a><span>Thoughtful hospitality, delivered.</span><button className="text-button" onClick={() => setStaffOpen(!staffOpen)}>Staff access</button><span>© THE WILLOW HOTEL</span></footer>
      {staffOpen && <section className="staff-panel section" aria-label="Staff order dashboard"><div><p className="eyebrow">STAFF PORTAL</p><h2>Order desk</h2><p>Staff credential stays in memory only and is sent only to authenticated backend endpoints.</p></div><div className="staff-work"><form onSubmit={(event) => { event.preventDefault(); void loadStaffOrders() }}><label>Staff API token<input type="password" value={staffToken} onChange={(event) => setStaffToken(event.target.value)} autoComplete="current-password" /></label><button className="button button-dark">Sign in & view orders</button></form>{staffOrders.map((staffOrder) => <article className="staff-order" key={staffOrder.id}><b>#{staffOrder.id} · {staffOrder.guest_name} · Room {staffOrder.room_number}</b><span>{staffOrder.status} · ${staffOrder.total_amount.toFixed(2)}</span><div>{staffOrder.status === 'confirmed' && <button onClick={() => void setStaffStatus(staffOrder.id, 'preparing')}>Start preparing</button>}{staffOrder.status === 'preparing' && <button onClick={() => void setStaffStatus(staffOrder.id, 'ready')}>Mark ready</button>}{['pending', 'confirmed', 'preparing'].includes(staffOrder.status) && <button onClick={() => void setStaffStatus(staffOrder.id, 'cancelled')}>Cancel</button>}</div></article>)}<div className="tag-tools"><h3>AprilTag room registry</h3><p>Register actual printed tag IDs for each room/floor using the camera setup. IDs are not inferred from room numbers.</p><form onSubmit={(event) => void saveTagMapping(event)}><label>Room<input required value={tagMapping.room_number} onChange={(event) => setTagMapping({ ...tagMapping, room_number: event.target.value })} /></label><label>Floor ID<input required value={tagMapping.floor_id} onChange={(event) => setTagMapping({ ...tagMapping, floor_id: event.target.value })} /></label><label>Tag family<input required value={tagMapping.tag_family} onChange={(event) => setTagMapping({ ...tagMapping, tag_family: event.target.value })} /></label><label>Observed tag ID<input type="number" min="0" required value={tagMapping.tag_id} onChange={(event) => setTagMapping({ ...tagMapping, tag_id: event.target.value })} /></label><button className="button button-dark">Save mapping</button></form><h4>Recent camera reports</h4>{apriltagEvents.length === 0 ? <p>No camera observations reported.</p> : apriltagEvents.slice(0, 8).map((record) => <p className="tag-event" key={record.id}>Room {record.room_number} · floor {record.floor_id} · {record.observed_family}:{record.observed_tag_id} · <b>{record.result}</b></p>)}</div></div></section>}
    </div>
  )
}

export default App
