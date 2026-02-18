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

    const agent =
        (selectedAgent && `${selectedAgent.id}` === `${id}` && selectedAgent) ||
        agents.find((a) => `${a.id}` === `${id}`)

    useEffect(() => {
        if (id) {
            fetchAgentById(id)
        }
    }, [fetchAgentById, id])

    return (
        <div className={`${styles.container} stack page-container`}>
            <div className="flex-between">
                <h2 style={{margin: 0}}>Профиль агента</h2>
                <Link to="/dashboard" className="btn">
                    ← Дашборд
                </Link>
            </div>
            {loading && <div className="status">Загрузка агента...</div>}
            {error && <div className="error">{error}</div>}
            <AgentProfile agent={agent}/>
        </div>
    )
}

