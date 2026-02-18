import {useState, useEffect} from 'react';
import {useNavigate} from 'react-router-dom';
import {API_BASE, getEvents} from '../../services/api';
import styles from './GroupChatPage.module.css';

export default function GroupChatPage() {
    const [groupChats, setGroupChats] = useState([]);
    const [agents, setAgents] = useState([]);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [selectedChat, setSelectedChat] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [chatEvents, setChatEvents] = useState([]);
    const [messageText, setMessageText] = useState('');
    const [sending, setSending] = useState(false);
    const [expandedChatIds, setExpandedChatIds] = useState(new Set());
    const [descriptionExpanded, setDescriptionExpanded] = useState(false);

    // Form states
    const [chatName, setChatName] = useState('');
    const [chatDescription, setChatDescription] = useState('');
    const [selectedAgents, setSelectedAgents] = useState([]);

    const navigate = useNavigate();

    // Fetch group chats and agents on component mount
    useEffect(() => {
        fetchGroupChats();
        fetchAgents();
    }, []);

    const fetchGroupChats = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                navigate('/login');
                return;
            }

            const response = await fetch(`${API_BASE}/api/group-chats`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const data = await response.json();
                setGroupChats(data);
            } else if (response.status === 401) {
                navigate('/login');
            } else {
                throw new Error('Failed to fetch group chats');
            }
        } catch (err) {
            setError('Ошибка при загрузке групповых чатов');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchAgents = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                navigate('/login');
                return;
            }

            const response = await fetch(`${API_BASE}/api/agents`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const data = await response.json();
                setAgents(data);
            } else if (response.status === 401) {
                navigate('/login');
            } else {
                throw new Error('Failed to fetch agents');
            }
        } catch (err) {
            setError('Ошибка при загрузке агентов');
            console.error(err);
        }
    };

    const handleCreateChat = async (e) => {
        e.preventDefault();

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                navigate('/login');
                return;
            }

            const response = await fetch(`${API_BASE}/api/group-chats`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: chatName,
                    description: chatDescription,
                    agent_ids: selectedAgents,
                }),
            });

            if (response.ok) {
                const newChat = await response.json();
                setGroupChats([...groupChats, newChat]);
                resetForm();
                setShowCreateForm(false);
            } else if (response.status === 401) {
                navigate('/login');
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Ошибка при создании чата');
            }
        } catch (err) {
            setError('Ошибка сети при создании чата');
            console.error(err);
        }
    };

    const handleDeleteChat = async (chatId) => {
        if (!window.confirm('Вы уверены, что хотите удалить этот чат?')) {
            return;
        }

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                navigate('/login');
                return;
            }

            const response = await fetch(`${API_BASE}/api/group-chats/${chatId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (response.ok) {
                setGroupChats(groupChats.filter(chat => chat.id !== chatId));
                if (selectedChat?.id === chatId) {
                    setSelectedChat(null);
                }
            } else if (response.status === 401) {
                navigate('/login');
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Ошибка при удалении чата');
            }
        } catch (err) {
            setError('Ошибка сети при удалении чата');
            console.error(err);
        }
    };

    const handleAgentSelect = (agentId) => {
        if (selectedAgents.includes(agentId)) {
            setSelectedAgents(selectedAgents.filter(id => id !== agentId));
        } else {
            setSelectedAgents([...selectedAgents, agentId]);
        }
    };

    const resetForm = () => {
        setChatName('');
        setChatDescription('');
        setSelectedAgents([]);
    };

    const selectChat = (chat) => {
        setSelectedChat(chat);
        setDescriptionExpanded(false);
    };

    const loadChatEvents = async (chat) => {
        if (!chat) {
            setChatEvents([]);
            return;
        }
        try {
            const allEvents = await getEvents();
            const ids = new Set(chat.agent_ids || []);
            const filtered = allEvents.filter(
                (ev) =>
                    (ev.actor_id && ids.has(ev.actor_id)) ||
                    (ev.target_id && ids.has(ev.target_id))
            );
            filtered.sort(
                (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
            );
            setChatEvents(filtered);
        } catch (err) {
            console.error('Ошибка при загрузке сообщений чата', err);
        }
    };

    useEffect(() => {
        if (selectedChat) {
            loadChatEvents(selectedChat);
        } else {
            setChatEvents([]);
        }
    }, [selectedChat]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!messageText.trim() || !selectedChat) return;

        try {
            setSending(true);
            const token = localStorage.getItem('token');
            if (!token) {
                navigate('/login');
                return;
            }

            await fetch(`${API_BASE}/api/group-chats/${selectedChat.id}/message`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: messageText,
                    emotion: null,
                }),
            });

            setMessageText('');
            if (selectedChat) {
                await loadChatEvents(selectedChat);
            }
        } catch (err) {
            setError('Ошибка при отправке сообщения в чат');
            console.error(err);
        } finally {
            setSending(false);
        }
    };

    const toggleChatDescription = (chatId) => {
        setExpandedChatIds((prev) => {
            const next = new Set(prev);
            if (next.has(chatId)) {
                next.delete(chatId);
            } else {
                next.add(chatId);
            }
            return next;
        });
    };

    return (
        <div className="stack page-container">
            <div className="flex-between">
                <h2 className="panel-title" style={{margin: 0}}>Групповые чаты</h2>
                <button
                    className="btn primary"
                    onClick={() => setShowCreateForm(!showCreateForm)}
                >
                    {showCreateForm ? 'Отмена' : 'Создать чат'}
                </button>
            </div>

            {error && (
                <div className="error">
                    {error}
                </div>
            )}

            {loading && <div className="status">Загрузка групповых чатов...</div>}

            {showCreateForm && (
                <section className={styles.panel}>
                    <div className={styles.panelHeader}>
                        <h3 className={styles.panelTitle}>Создать новый чат</h3>
                    </div>

                    <form className={styles.createForm} onSubmit={handleCreateChat}>
                        <div className={styles.formGroup}>
                            <label htmlFor="chatName">Название чата</label>
                            <input
                                id="chatName"
                                type="text"
                                className="input"
                                value={chatName}
                                onChange={(e) => setChatName(e.target.value)}
                                required
                                placeholder="Введите название чата"
                            />
                        </div>

                        <div className={styles.formGroup}>
                            <label htmlFor="chatDescription">Описание</label>
                            <textarea
                                id="chatDescription"
                                className={styles.textarea}
                                value={chatDescription}
                                onChange={(e) => setChatDescription(e.target.value)}
                                placeholder="Опишите тему обсуждения в этом чате"
                                rows="3"
                            />
                        </div>

                        <div className={styles.formGroup}>
                            <label>Участники (агенты)</label>
                            <div className={styles.agentsList}>
                                {agents.map((agent) => (
                                    <div key={agent.id} className={styles.agentItem}>
                                        <label>
                                            <input
                                                type="checkbox"
                                                checked={selectedAgents.includes(agent.id)}
                                                onChange={() => handleAgentSelect(agent.id)}
                                            />
                                            <span>{agent.name}</span>
                                        </label>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className={styles.formActions}>
                            <button type="submit" className="btn primary">
                                Создать чат
                            </button>
                            <button
                                type="button"
                                onClick={resetForm}
                                className="btn"
                            >
                                Сброс
                            </button>
                        </div>
                    </form>
                </section>
            )}

            <div className={`${styles.content} agent-chat`}>
                <section className={`${styles.panel} ${styles.chatList}`}>
                    <div className={styles.panelHeader}>
                        <h3 className={styles.panelTitle}>Список чатов</h3>
                    </div>
                    {groupChats.length === 0 ? (
                        <p className="empty">У вас пока нет групповых чатов. Создайте первый!</p>
                    ) : (
                        <ul className={styles.chats}>
                            {groupChats.map((chat) => (
                                <li
                                    key={chat.id}
                                    className={`${styles.chatItem} ${
                                        selectedChat?.id === chat.id ? styles.selected : ''
                                    }`}
                                    onClick={() => selectChat(chat)}
                                >
                                    <div className={styles.chatHeader}>
                                        <h3>{chat.name}</h3>
                                        <button
                                            className="btn danger"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteChat(chat.id);
                                            }}
                                        >
                                            Удалить
                                        </button>
                                    </div>
                                    {chat.description && (
                                        <div className={styles.chatDescriptionWrapper}>
                                            {!expandedChatIds.has(chat.id) ? (
                                                <button
                                                    type="button"
                                                    className={styles.toggleDescription}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        toggleChatDescription(chat.id);
                                                    }}
                                                >
                                                    Показать описание
                                                </button>
                                            ) : (
                                                <>
                                                    <p className={styles.chatDescription}>
                                                        {chat.description}
                                                    </p>
                                                    <button
                                                        type="button"
                                                        className={styles.toggleDescription}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            toggleChatDescription(chat.id);
                                                        }}
                                                    >
                                                        Свернуть
                                                    </button>
                                                </>
                                            )}
                                        </div>
                                    )}
                                    <div className={styles.chatMeta}>
                                        <span>Агентов: {chat.agent_ids.length}</span>
                                        <span>
                      Создан: {new Date(chat.created_at).toLocaleDateString()}
                    </span>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </section>

                <section className={`${styles.panel} ${styles.chatView}`}>
                    {selectedChat ? (
                        <div className={styles.selectedChat}>
                            <div className={styles.panelHeader}>
                                <h3 className={styles.panelTitle}>{selectedChat.name}</h3>
                            </div>

                            {selectedChat.description && (
                                <div className={styles.selectedChatDescriptionWrapper}>
                                    {!descriptionExpanded ? (
                                        <button
                                            type="button"
                                            className={styles.toggleDescription}
                                            onClick={() => setDescriptionExpanded(true)}
                                        >
                                            Показать описание
                                        </button>
                                    ) : (
                                        <>
                                            <p className={styles.selectedChatDescription}>
                                                {selectedChat.description}
                                            </p>
                                            <button
                                                type="button"
                                                className={styles.toggleDescription}
                                                onClick={() => setDescriptionExpanded(false)}
                                            >
                                                Свернуть
                                            </button>
                                        </>
                                    )}
                                </div>
                            )}

                            <div className={styles.selectedChatAgents}>
                                <h3>Участники чата</h3>
                                <ul>
                                    {selectedChat.agent_ids.map((agentId) => {
                                        const agent = agents.find((a) => a.id === agentId);
                                        return agent ? <li key={agentId}>{agent.name}</li> : null;
                                    })}
                                </ul>
                            </div>

                            <div className={styles.chatMessages}>
                                <h3>Сообщения</h3>
                                <div className={styles.messagesList}>
                                    {chatEvents.length === 0 ? (
                                        <p className={styles.noMessages}>Сообщений пока нет</p>
                                    ) : (
                                        <ul>
                                            {chatEvents.map((event) => (
                                                <li key={event.id} className={styles.messageItem}>
                                                    <div className={styles.messageBubble}>
                                                        <div className={styles.messageText}>
                                                            {event.description}
                                                        </div>
                                                        <div className={styles.messageMeta}>
                                <span className={styles.messageTime}>
                                  {event.timestamp
                                      ? new Date(
                                          event.timestamp,
                                      ).toLocaleTimeString()
                                      : ''}
                                </span>
                                                        </div>
                                                    </div>
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                                </div>

                                <form
                                    className={styles.messageForm}
                                    onSubmit={handleSendMessage}
                                >
                                    <div className={styles.formRow}>
                                        <input
                                            type="text"
                                            className="input"
                                            value={messageText}
                                            onChange={(e) => setMessageText(e.target.value)}
                                            placeholder="Введите сообщение агенту"
                                        />
                                        <button
                                            type="submit"
                                            className="btn primary"
                                            disabled={
                                                sending || !selectedChat || !messageText.trim()
                                            }
                                        >
                                            Отправить
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    ) : (
                        <div className={styles.noChatSelected}>
                            <p>Выберите чат из списка или создайте новый</p>
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}

