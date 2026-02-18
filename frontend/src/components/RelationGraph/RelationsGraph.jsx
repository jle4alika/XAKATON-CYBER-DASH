import {useEffect, useMemo, useRef, useState} from 'react'
import {useNavigate} from 'react-router-dom'
import ForceGraph2D from 'react-force-graph-2d'
import styles from './RelationsGraph.module.css'

const moodToColor = (mood = 0) => {
    if (mood >= 0.7) return '#22c55e'
    if (mood >= 0.4) return '#eab308'
    return '#ef4444'
}

export default function RelationsGraph({agents = [], relations = []}) {
    const navigate = useNavigate()
    const [hoverNode, setHoverNode] = useState(null)
    const [hoverLink, setHoverLink] = useState(null)
    const fgRef = useRef(null)
    const panelRef = useRef(null)
    const [cursorPos, setCursorPos] = useState({x: 0, y: 0})
    const [graphWidth, setGraphWidth] = useState(400)
    const graphHeight = 360

    const data = useMemo(
        () => {
            const nodeMap = new Map()
            agents.forEach((a) => {
                if (!a?.id) return
                nodeMap.set(a.id, {
                    id: a.id,
                    name: a.name,
                    mood: a.mood ?? 0.5,
                    energy: a.energy ?? 50,
                    activity: a.activity ?? a.energy ?? 40,
                })
            })
            relations.forEach((r) => {
                const source = r.source || r.agentA || r.from
                const target = r.target || r.agentB || r.to
                if (source && !nodeMap.has(source)) {
                    nodeMap.set(source, {id: source, name: source, mood: 0.5, energy: 50, activity: 40})
                }
                if (target && !nodeMap.has(target)) {
                    nodeMap.set(target, {id: target, name: target, mood: 0.5, energy: 50, activity: 40})
                }
            })

            const nodes = Array.from(nodeMap.values())
            const links = relations
                .filter((r) => (r.source || r.agentA || r.from) && (r.target || r.agentB || r.to))
                .map((r) => ({
                    source: r.source || r.agentA || r.from,
                    target: r.target || r.agentB || r.to,
                    affinity: Number(r.affinity ?? r.strength ?? 0.2),
                    label: r.label || r.type || 'relation',
                }))

            return {nodes, links}
        },
        [agents, relations],
    )

    useEffect(() => {
        // Подгоняем ширину графа под ширину панели, чтобы отступы слева/справа были одинаковыми.
        const updateSize = () => {
            if (!panelRef.current) return
            const rect = panelRef.current.getBoundingClientRect()
            // Немного уменьшаем, чтобы оставить внутренние отступы от границ панели
            setGraphWidth(Math.max(200, rect.width - 32))
        }

        updateSize()
        window.addEventListener('resize', updateSize)
        return () => window.removeEventListener('resize', updateSize)
    }, [])

    useEffect(() => {
        if (!fgRef.current) return
        if (!data.nodes.length) return
        const t = setTimeout(() => {
            fgRef.current?.zoomToFit(400, 60)
        }, 150)
        return () => clearTimeout(t)
    }, [data.nodes.length, data.links.length])

    const handleMouseMove = (event) => {
        if (!panelRef.current) return
        const rect = panelRef.current.getBoundingClientRect()
        const x = event.clientX - rect.left
        const y = event.clientY - rect.top
        setCursorPos({x, y})
    }

    return (
        <div className={styles.panel} ref={panelRef} onMouseMove={handleMouseMove}>
            <div className={styles.panelHeader}>
                <h3 className={styles.panelTitle}>Граф отношений</h3>
            </div>
            {data.nodes.length === 0 ? (
                <div className={styles.empty}>Нет данных для графа</div>
            ) : (
                <ForceGraph2D
                    ref={fgRef}
                    width={graphWidth}
                    height={graphHeight}
                    graphData={data}
                    backgroundColor="transparent"
                    linkColor={(link) => (link.affinity >= 0 ? 'rgba(34,197,94,0.6)' : 'rgba(239,68,68,0.6)')}
                    linkWidth={(link) => Math.max(1, Math.abs(link.affinity || 0.3) * 4)}
                    onLinkHover={(link) => setHoverLink(link || null)}
                    onNodeClick={(node) => navigate(`/agent/${node.id}`)}
                    onNodeHover={(node) => setHoverNode(node || null)}
                    nodeCanvasObject={(node, ctx, globalScale) => {
                        const radius = 6 + Math.min(14, (node.activity ?? 40) / 10)
                        ctx.beginPath()
                        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false)
                        ctx.fillStyle = moodToColor(node.mood)
                        ctx.fill()
                        ctx.strokeStyle = 'rgba(255,255,255,0.1)'
                        ctx.stroke()
                        const label = node.name || node.id
                        const fontSize = 12 / globalScale
                        ctx.font = `${fontSize}px Inter`
                        ctx.fillStyle = '#e2e8f0'
                        ctx.fillText(label, node.x + radius + 4, node.y + fontSize / 2)
                    }}
                />
            )}
            {hoverLink && (
                <div
                    className={styles.tooltip}
                    style={{left: cursorPos.x + 12, top: cursorPos.y + 12}}
                >
                    <div style={{fontWeight: 700}}>
                        {hoverLink.source?.name || hoverLink.source?.id} ↔ {hoverLink.target?.name || hoverLink.target?.id}
                    </div>
                    <div>Дружелюбность: {hoverLink.affinity?.toFixed(2)}</div>
                    <div className={styles.muted}>{hoverLink.label}</div>
                </div>
            )}
            {hoverNode && !hoverLink && (
                <div
                    className={styles.tooltip}
                    style={{left: cursorPos.x + 12, top: cursorPos.y + 12}}
                >
                    <div className={styles.muted}>Узел</div>
                    <div style={{fontWeight: 700}}>{hoverNode.name}</div>
                    <div>Настроение: {hoverNode.mood.toFixed(2)}</div>
                    <div>Энергия: {Math.round(hoverNode.energy)}</div>
                    <div>Активность: {Math.round(hoverNode.activity)}</div>
                </div>
            )}
        </div>
    )
}

