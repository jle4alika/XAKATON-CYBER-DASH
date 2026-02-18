import {useMemo, useState} from 'react'
import {AnimatePresence, motion} from 'framer-motion'
import MemoryList from '../MemoryList/MemoryList.jsx'
import MessageInput from '../MessangeInput/MessageInput.jsx'
import styles from './AgentProfile.module.css'

const moodToLabel = (mood = 0) => {
    if (mood >= 0.7) return 'радостное'
    if (mood >= 0.4) return 'нейтральное'
    return 'подавленное'
}

const moodToColor = (mood = 0) => {
    if (mood >= 0.7) return 'var(--accent-green)'
    if (mood >= 0.4) return 'var(--accent-yellow)'
    return 'var(--accent-red)'
}

const tabs = [
    {id: 'memory', label: 'Память'},
    {id: 'plans', label: 'Планы'},
    {id: 'interactions', label: 'Взаимодействия'},
]

export default function AgentProfile({agent}) {
    const [activeTab, setActiveTab] = useState('memory')
    const moodLabel = useMemo(() => moodToLabel(agent?.mood), [agent])

    if (!agent) {
        return <div className={styles.empty}>Агент не найден</div>
    }

    return (
        <div className={styles.stack}>
            <div className={styles.card} style={{borderColor: 'rgba(56, 189, 248, 0.25)'}}>
                <div className={styles.flexBetween}>
                    <div>
                        <h2 style={{margin: 0}}>{agent.name}</h2>
                        <div className={styles.muted}>Настроение: {moodLabel}</div>
                        <div className={styles.muted}>Энергия: {Math.round(agent.energy ?? 0)}</div>
                    </div>
                    <span className={styles.pill}>
            <span className={styles.moodIndicator} style={{background: moodToColor(agent.mood)}}/>
                        {(agent.mood ?? 0).toFixed(2)}
          </span>
                </div>
            </div>

            <div>
                <div className={styles.tabs}>
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            className={[styles.tab, activeTab === tab.id && styles.tabActive].filter(Boolean).join(' ')}
                            type="button"
                            onClick={() => setActiveTab(tab.id)}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                <div className={styles.panel}>
                    <AnimatePresence mode="wait">
                        {activeTab === 'memory' && (
                            <motion.div
                                key="memory"
                                initial={{opacity: 0, y: 10}}
                                animate={{opacity: 1, y: 0}}
                                exit={{opacity: 0, y: -6}}
                            >
                                <MemoryList memories={agent.memories || []}/>
                            </motion.div>
                        )}
                        {activeTab === 'plans' && (
                            <motion.div
                                key="plans"
                                initial={{opacity: 0, y: 10}}
                                animate={{opacity: 1, y: 0}}
                                exit={{opacity: 0, y: -6}}
                                className={styles.stack}
                            >
                                {(agent.plans || []).length === 0 &&
                                    <div className={styles.empty}>Планов пока нет</div>}
                                {(agent.plans || []).map((plan, idx) => {
                                    const statusMap = {
                                        'active': 'активен',
                                        'planned': 'запланирован',
                                        'in-progress': 'в процессе',
                                        'completed': 'завершен',
                                        'pending': 'ожидает',
                                    }
                                    const statusText = statusMap[plan.status] || plan.status || 'ожидает'
                                    return (
                                        <div key={idx} className={styles.eventItem}>
                                            <div>{plan.title || plan.description}</div>
                                            <div className={styles.muted}>статус: {statusText}</div>
                                        </div>
                                    )
                                })}
                            </motion.div>
                        )}
                        {activeTab === 'interactions' && (
                            <motion.div
                                key="interactions"
                                initial={{opacity: 0, y: 10}}
                                animate={{opacity: 1, y: 0}}
                                exit={{opacity: 0, y: -6}}
                                className={styles.stack}
                            >
                                {(agent.interactions || []).length === 0 &&
                                    <div className={styles.empty}>Нет взаимодействий</div>}
                                {(agent.interactions || []).map((item, idx) => (
                                    <div key={idx} className={styles.eventItem}>
                                        <div>{item.description}</div>
                                        <div className={styles.muted}>
                                            с {item.with || item.partner || 'неизвестно'} ·{' '}
                                            {item.timestamp ? new Date(item.timestamp).toLocaleString() : 'только что'}
                                        </div>
                                    </div>
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>

            <div className={styles.panel}>
                <h3 style={{marginTop: 0}}>Отправитf\ь сообщение</h3>
                <MessageInput agentId={agent.id}/>
            </div>
        </div>
    )
}

