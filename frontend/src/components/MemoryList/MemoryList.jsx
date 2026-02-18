import styles from './MemoryList.module.css'

export default function MemoryList({ memories }) {
  if (!memories || memories.length === 0) {
    return <div className={styles.empty}>Воспоминаний пока нет</div>
  }

  return (
    <div className={styles.stack}>
      {memories.map((memory, idx) => (
        <div key={memory.id || idx} className={styles.eventItem}>
          <div>{memory.description || memory.text}</div>
          <div className={styles.muted}>
            эмоция: {memory.emotion || 'нейтрально'} ·{' '}
            {memory.timestamp ? new Date(memory.timestamp).toLocaleString() : 'недавно'}
          </div>
        </div>
      ))}
    </div>
  )
}

