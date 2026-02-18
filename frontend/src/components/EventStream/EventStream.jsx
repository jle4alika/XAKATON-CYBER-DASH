import {useEffect, useRef, useState} from 'react'
import {AnimatePresence, motion} from 'framer-motion'
import useEventStore from '../../store/eventStore.js'
import useAgentStore from '../../store/agentStore.js'
import {connectEventStream} from '../../services/websocket.js'
import styles from './EventStream.module.css'

export default function EventStream() {
    const events = useEventStore((state) => state.events)
    const loading = useEventStore((state) => state.loading)
    const error = useEventStore((state) => state.error)
    const fetchEvents = useEventStore((state) => state.fetchEvents)
    const addEvent = useEventStore((state) => state.addEvent)

    const updateAgentFromEvent = useAgentStore((state) => state.updateAgentFromEvent)
    const setRelations = useAgentStore((state) => state.setRelations)

    const listRef = useRef(null)
    const [connected, setConnected] = useState(false)
    const [wsKey, setWsKey] = useState(0)

    useEffect(() => {
        fetchEvents()
    }, [fetchEvents])

    useEffect(() => {
        const connection = connectEventStream((payload) => {
            if (!payload?.type) return
            if (payload.type === 'event_created') {
                addEvent(payload.data)
            }
            if (payload.type === 'agent_update') {
                updateAgentFromEvent(payload.data)
            }
            if (payload.type === 'relation_changed') {
                setRelations(payload.data)
            }
        }, {onStatus: (status) => setConnected(status === 'connected')})
        return () => {
            connection.close()
        }
    }, [addEvent, setRelations, updateAgentFromEvent, wsKey])

    useEffect(() => {
        const handler = () => setWsKey((k) => k + 1)
        window.addEventListener('ws:reconnect', handler)
        return () => window.removeEventListener('ws:reconnect', handler)
    }, [])

    useEffect(() => {
        const el = listRef.current
        if (el) {
            el.scrollTo({top: el.scrollHeight, behavior: 'smooth'})
        }
    }, [events])

    return (
        <div className={styles.eventdiv}>
            <section className={styles.panel}>
                <div className={styles.panelHeader}>
                    <h3 className={styles.panelTitle}>Лента событий</h3>
                </div>
                {loading && <div className={styles.status}>Загрузка событий...</div>}
                {!loading && !events.length && <div className={styles.empty}>Событий нет</div>}
                <div className={`${styles.eventList} ${styles.stack}`} ref={listRef}>
                    <AnimatePresence initial={false}>
                        {events.map((event) => (
                            <motion.div
                                key={event.id || event.timestamp || Math.random()}
                                layout
                                initial={{opacity: 0, y: 8}}
                                animate={{opacity: 1, y: 0}}
                                exit={{opacity: 0, scale: 0.97}}
                                transition={{duration: 0.18}}
                                className={styles.eventItem}
                            >
                                <div className={styles.eventTime}>
                                    {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : '—'}
                                </div>
                                <div>{event.description || event.text}</div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            </section>
        </div>

    )
}

