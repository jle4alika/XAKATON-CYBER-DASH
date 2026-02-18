import {useEffect} from 'react'
import {Link, useParams} from 'react-router-dom'
import AgentProfile from '../../components/AgentProfile/AgentProfile.jsx'
import useAgentStore from '../../store/agentStore'
import styles from './AgentPage.module.css'

export default function AgentPage() {
    const {id} = useParams()
    const agents = useAgentStore((state) => state.agents)
    const selectedAgent = useAgentStore((state) => state.selectedAgent)
    const loading = useAgentStore((state) => state.loading)
    const error = useAgentStore((state) => state.error)
    const fetchAgentById = useAgentStore((state) => state.fetchAgentById)

    // Всегда используем selectedAgent если он есть и соответствует ID, иначе ищем в списке
    // selectedAgent содержит полные данные включая планы, взаимодействия и память
    const agent = selectedAgent && `${selectedAgent.id}` === `${id}`
        ? selectedAgent
        : agents.find((a) => `${a.id}` === `${id}`)

    // Отладочное логирование
    console.log('AgentPage - agent:', agent)
    console.log('AgentPage - selectedAgent:', selectedAgent)
    console.log('AgentPage - agent plans:', agent?.plans)

    useEffect(() => {
        if (id) {
            fetchAgentById(id)
        }
    }, [fetchAgentById, id])

    return (
        <div className={`${styles.container} stack page-container`}>
            <div className={styles.header}>
                <h2 className={styles.title}>Профиль агента</h2>
                <Link to="/dashboard" className={styles.backButton}>
                    ← Дашборд
                </Link>
            </div>
            {loading && <div className="status">Загрузка агента...</div>}
            {error && <div className="error">{error}</div>}
            <div className={styles.profilePanel}>
                <AgentProfile agent={agent}/>
            </div>
        </div>
    )
}

