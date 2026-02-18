import { useState } from 'react'
import { postMessage } from '../../services/api.js'
import styles from './MessageInput.module.css'

export default function MessageInput({ agentId, onSent }) {
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)

  const handleSend = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    setSending(true)
    setError(null)
    try {
      const payload = { message: text.trim() }
      await postMessage(agentId, payload)
      setText('')
      onSent?.(payload)
    } catch (err) {
      setError(err.message || 'Failed to send message')
    } finally {
      setSending(false)
    }
  }

  return (
    <form className={styles.stack} onSubmit={handleSend}>
      <input
        className={styles.input}
        placeholder="Привет, агент..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        aria-label="message"
      />
      <div className={styles.flexBetween}>
        <button type="submit" className={`${styles.btn} ${styles.btnPrimary}`} disabled={sending || !text.trim()}>
          {sending ? 'Отправка...' : 'Отправить'}
        </button>
        {error && <div className={styles.error}>{error}</div>}
      </div>
    </form>
  )
}

