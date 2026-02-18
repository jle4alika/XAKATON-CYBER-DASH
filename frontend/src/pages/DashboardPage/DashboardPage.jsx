import AgentGrid from '../../components/AgentGrid/AgentGrid.jsx'
import EventStream from '../../components/EventStream/EventStream.jsx'
import TimeControlPanel from '../../components/TimeControlPanel/TimeControlPanel.jsx'
import GlobalActionsPanel from '../../components/GlobalActionPanel/GlobalActionsPanel.jsx'
import AddAgentForm from '../../components/AddAgentForm/AddAgentForm.jsx'
import style from './DashboardPage.module.css'

export default function DashboardPage() {
    return (
        <div className="stack page-container">
            <div className={style.GodHand}>
                <GlobalActionsPanel/>
            </div>
            <div className="panel-agent">
                <div className="panel-header">
                    <h2 className="panel-title">Жизнь агентов</h2>
                    <AddAgentForm/>
                </div>
                <AgentGrid/>
            </div>

            <div className="row">
                <EventStream/>
                <TimeControlPanel/>
            </div>
        </div>
    )
}

