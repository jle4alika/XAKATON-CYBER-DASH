import {useEffect} from 'react'
import RelationsGraph from '../../components/RelationGraph/RelationsGraph.jsx'
import useAgentStore from '../../store/agentStore'
import styles from './RelationsPage.module.css'

export default function RelationsPage() {
    const agents = useAgentStore((state) => state.agents)
    const relations = useAgentStore((state) => state.relations)
    const fetchAgents = useAgentStore((state) => state.fetchAgents)
    const fetchRelations = useAgentStore((state) => state.fetchRelations)

    useEffect(() => {
        if (!agents.length) {
            fetchAgents()
        }
        fetchRelations()
    }, [agents.length, fetchAgents, fetchRelations])

    return (
        <div className={`${styles.container} stack page-container`}>
            <section>
                <div className="section-title">
                    <h2>Граф отношений</h2>
                    <span className="muted">наведите на связь, чтобы увидеть дружелюбность</span>
                </div>
                <RelationsGraph agents={agents} relations={relations}/>
            </section>
        </div>
    )
}

