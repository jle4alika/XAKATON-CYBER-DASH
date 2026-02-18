import useAgentStore from '../../store/agentStore.js'
import useEventStore from '../../store/eventStore.js'
import styles from './GlobalActionsPanel.module.css'

export default function GlobalActionsPanel() {
    const fetchAgents = useAgentStore((s) => s.fetchAgents)
    const fetchRelations = useAgentStore((s) => s.fetchRelations)
    const fetchEvents = useEventStore((s) => s.fetchEvents)

    // const handleReconnectWs = () => {
    //     window.dispatchEvent(new CustomEvent('ws:reconnect'))
    // }

    return (
        <section className={`${styles.panel} ${styles.stack}`}>
            <div className={styles.panelHeader}>
                <h3 className={styles.panelTitle}>Глобальные действия</h3>
            </div>
            <div className={styles.flex}>
                <button className={styles.btn} type="button" onClick={() => fetchAgents()}>Обновить агентов</button>
                <button className={styles.btn} type="button" onClick={() => fetchRelations()}>Обновить отношения
                </button>
                <button className={styles.btn} type="button" onClick={() => fetchEvents()}>Обновить события</button>
                {/*<button className={styles.btn} type="button" onClick={handleReconnectWs}>Переподключить WS</button>*/}
            </div>
        </section>
    )
}

