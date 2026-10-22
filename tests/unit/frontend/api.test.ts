import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { request, ApiError } from '../../../fastapi-todo-react-frontend/src/lib/api'
import { saveSession, loadSession, SESSION_EXPIRED_EVENT } from '../../../fastapi-todo-react-frontend/src/lib/session'
import { todoService } from '../../../fastapi-todo-react-frontend/src/services/todoService'
import { authService } from '../../../fastapi-todo-react-frontend/src/services/authService'

const jsonResponse = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

beforeEach(() => localStorage.clear())
afterEach(() => vi.unstubAllGlobals())

describe('session storage', () => {
  it('round-trips and expires', () => {
    saveSession({ token: 't', user: { id: 1, email: 'a@b.c', full_name: null, role: 'admin' }, expiresAt: Date.now() + 60_000 })
    expect(loadSession()?.token).toBe('t')
    saveSession({ token: 'old', user: { id: 1, email: 'a@b.c', full_name: null, role: 'admin' }, expiresAt: Date.now() - 1 })
    expect(loadSession()).toBeNull()
  })
  it('survives corrupt storage', () => {
    localStorage.setItem('todo.session.v1', '{not json')
    expect(loadSession()).toBeNull()
  })
})

describe('request()', () => {
  it('attaches the bearer token and unwraps data', async () => {
    saveSession({ token: 'abc', user: { id: 1, email: 'a@b.c', full_name: null, role: 'admin' }, expiresAt: Date.now() + 60_000 })
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { status: 200, message: 'ok', data: [1, 2] }))
    vi.stubGlobal('fetch', fetchMock)
    expect(await request<number[]>('/todos')).toEqual([1, 2])
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/todos')
    expect(init.headers.Authorization).toBe('Bearer abc')
  })

  it('surfaces backend message and clears session + notifies on 401', async () => {
    saveSession({ token: 'abc', user: { id: 1, email: 'a@b.c', full_name: null, role: 'admin' }, expiresAt: Date.now() + 60_000 })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(401, { status: 401, message: 'Invalid or expired token' })))
    const expired = vi.fn()
    window.addEventListener(SESSION_EXPIRED_EVENT, expired)
    await expect(request('/todos')).rejects.toMatchObject({ name: 'ApiError', status: 401, message: 'Invalid or expired token' })
    expect(expired).toHaveBeenCalledOnce()
    expect(loadSession()).toBeNull()
    window.removeEventListener(SESSION_EXPIRED_EVENT, expired)
  })

  it('does not treat a failed login as an expired session', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(401, { message: 'Invalid email or password' })))
    const expired = vi.fn()
    window.addEventListener(SESSION_EXPIRED_EVENT, expired)
    await expect(authService.login('a@b.c', 'x')).rejects.toBeInstanceOf(ApiError)
    expect(expired).not.toHaveBeenCalled()
    window.removeEventListener(SESSION_EXPIRED_EVENT, expired)
  })

  it('copes with non-JSON error bodies (e.g. proxy 502)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>Bad gateway</html>', { status: 502 })))
    await expect(request('/todos')).rejects.toMatchObject({ status: 502, message: 'Request failed (502)' })
  })
})

describe('todoService', () => {
  it('uses the right verbs and paths', async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(jsonResponse(200, { status: 200, message: '', data: {} })))
    vi.stubGlobal('fetch', fetchMock)
    await todoService.createTodo('t', 'd')
    await todoService.updateTodo(5, 't', 'd', true)
    await todoService.deleteTodo(5)
    const calls = fetchMock.mock.calls.map(([u, i]) => `${i.method ?? 'GET'} ${u}`)
    expect(calls).toEqual(['POST /api/todos', 'PUT /api/todos/update/5', 'DELETE /api/todos/delete/5'])
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({ title: 't', description: 'd', is_completed: true })
  })

  it('login maps expires_in to an absolute expiry', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(200, { status: 200, message: '', data: {
      access_token: 'tok', token_type: 'bearer', expires_in: 3600, user: { id: 1, email: 'a@b.c', full_name: null, role: 'admin' } } })))
    const s = await authService.login('a@b.c', 'x')
    expect(s.token).toBe('tok')
    expect(s.expiresAt).toBeGreaterThan(Date.now() + 3_500_000)
  })
})
