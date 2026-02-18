import {useEffect} from 'react'
import useAgentStore from '../../store/agentStore.js'
import AgentCard from '../AgentCard/AgentCard.jsx'
import styles from './AgentGrid.module.css'

/**
 * Сетка карточек агентов на дашборде.
 *
 * При первом рендере подгружает агентов из стора (если их ещё нет),
 * отображает статус загрузки и пустое состояние, когда список пуст.
 */
export default function AgentGrid() {
    const agents = useAgentStore((state) => state.agents)
    const loading = useAgentStore((state) => state.loading)
    const error = useAgentStore((state) => state.error)
    const fetchAgents = useAgentStore((state) => state.fetchAgents)

    useEffect(() => {
        if (!agents.length) {
            fetchAgents()
        }
    }, [agents.length, fetchAgents])

    return (
        <div className={styles.stack}>
            {loading && <div className={styles.status}>Загрузка агентов...</div>}
            {!loading && !agents.length && <div className={styles.empty}>Агентов нет</div>}
            <div className={styles.grid}>
                {agents.map((agent) => (
                    <AgentCard key={agent.id} agent={agent}/>
                ))}
            </div>
        </div>
    )
}

