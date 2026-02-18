import {Routes, Route} from 'react-router-dom'
import Navbar from './components/Navbar/Navbar.jsx'
import DashboardPage from './pages/DashboardPage/DashboardPage'
import RelationsPage from './pages/RelationsPage/RelationsPage'
import AgentPage from './pages/AgentPage/AgentPage'
import SettingsPage from './pages/SettingsPage/SettingsPage'
import GroupChatPage from './pages/GroupChatPage/GroupChatPage'
import NotFoundPage from './pages/NotFoundPage/NotFoundPage'
import MainPage from "./pages/MainPage/MainPage";
import LoginPage from './pages/LoginPage/LoginPage'
import RegisterPage from './pages/RegisterPage/RegisterPage'
import AuthWrapper from './components/AuthWrapper.jsx'
import './index.css'

/**
 * Корневой компонент приложения.
 *
 * Здесь описываются все маршруты, общая навигация (Navbar)
 * и обёртка AuthWrapper, которая защищает приватные страницы.
 */
function App() {
    return (
        <div className="app">
            <Navbar/>
            <main className="">
                <Routes>
                    <Route path="/" element={<MainPage/>}/>
                    <Route path="/login" element={<LoginPage/>}/>
                    <Route path="/register" element={<RegisterPage/>}/>
                    <Route path="/dashboard" element={
                        <AuthWrapper>
                            <DashboardPage/>
                        </AuthWrapper>
                    }/>
                    <Route path="/group-chat" element={
                        <AuthWrapper>
                            <GroupChatPage/>
                        </AuthWrapper>
                    }/>
                    {/* Individual agent chat is now accessible through the group chat interface */}
                    <Route path="/relations" element={
                        <AuthWrapper>
                            <RelationsPage/>
                        </AuthWrapper>
                    }/>
                    {/* Детальный профиль агента по его ID */}
                    <Route path="/agent/:id" element={
                        <AuthWrapper>
                            <AgentPage/>
                        </AuthWrapper>
                    }/>
                    <Route path="/settings" element={
                        <AuthWrapper>
                            <SettingsPage/>
                        </AuthWrapper>
                    }/>
                    <Route path="*" element={<NotFoundPage/>}/>
                </Routes>
            </main>
        </div>
    )
}

export default App
