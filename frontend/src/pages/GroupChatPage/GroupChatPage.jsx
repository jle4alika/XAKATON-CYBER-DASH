import {useState, useEffect, useRef, useCallback} from 'react';
import {useNavigate} from 'react-router-dom';
import {API_BASE, getEvents} from '../../services/api';
import {connectEventStream} from '../../services/websocket';
import styles from './GroupChatPage.module.css';

export default function GroupChatPage() {
    const [groupChats, setGroupChats] = useState([]);
    const [agents, setAgents] = useState([]);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [selectedChat, setSelectedChat] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [chatEvents, setChatEvents] = useState([]);
    const [allChatEvents, setAllChatEvents] = useState([]);
    const [displayedCount, setDisplayedCount] = useState(50);
    const [loadingMore, setLoadingMore] = useState(false);
    const [messageText, setMessageText] = useState('');
    const [sending, setSending] = useState(false);

    const messagesEndRef = useRef(null);
    const messagesContainerRef = useRef(null);
    const loadMoreTriggerRef = useRef(null);

    // Form states
    const [chatName, setChatName] = useState('');
    const [chatDescription, setChatDescription] = useState('');
    const [selectedAgents, setSelectedAgents] = useState([]);

    const navigate = useNavigate();
    const [authToken, setAuthToken] = useState(() => localStorage.getItem('token'));

    // Keep token in sync (login/logout in another tab, token refresh, etc.)
    useEffect(() => {
        const syncToken = () => setAuthToken(localStorage.getItem('token'));
        window.addEventListener('storage', syncToken);
        window.addEventListener('focus', syncToken);
        const intervalId = setInterval(syncToken, 1000);
        return () => {
            window.removeEventListener('storage', syncToken);
            window.removeEventListener('focus', syncToken);
            clearInterval(intervalId);
        };
    }, []);

    // Fetch group chats and agents when token changes / page becomes active
    useEffect(() => {
        if (!authToken) {
            navigate('/login');
            return;
        }
        setError('');
        setSelectedChat(null);
        setShowCreateForm(false);
        resetForm();
        fetchGroupChats(authToken);
        fetchAgents(authToken);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [authToken]);

    const fetchGroupChats = async (tokenOverride) => {
        try {
            const token = tokenOverride ?? localStorage.getItem('token');
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

    const fetchAgents = async (tokenOverride) => {
        try {
            const token = tokenOverride ?? localStorage.getItem('token');
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
            const token = authToken ?? localStorage.getItem('token');
            if (!token) {
                navigate('/login');
                return;
            }

            // Guard against stale agent list: only allow selecting agents visible for current token
            const allowedAgentIdSet = new Set((agents || []).map((a) => String(a.id)));
            const sanitizedSelectedAgents = (selectedAgents || []).map(String).filter((id) => allowedAgentIdSet.has(id));
            if (sanitizedSelectedAgents.length !== (selectedAgents || []).length) {
                setError('Список агентов устарел (возможна смена пользователя). Обновите страницу и выберите агентов заново.');
                // Best-effort refresh
                fetchAgents(token);
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
                    agent_ids: sanitizedSelectedAgents,
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
                const detail = errorData?.detail;
                if (typeof detail === 'string' && detail.includes("Agents not found or don't belong to user")) {
                    setError('Вы выбрали агентов, которые не принадлежат текущему пользователю. Обновите страницу и выберите агентов заново.');
                    // Best-effort refresh
                    fetchAgents(token);
                } else {
                    setError(detail || 'Ошибка при создании чата');
                }
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
    };

    const loadChatEvents = async (chat, reset = true) => {
        if (!chat) {
            setChatEvents([]);
            setAllChatEvents([]);
            setDisplayedCount(50);
            return;
        }
        try {
            const allEvents = await getEvents();
            const ids = new Set(chat.agent_ids || []);
            const chatIdStr = String(chat.id);

            const filtered = allEvents.filter((ev) => {
                // Проверяем события от агентов чата
                if (ev.actor_id && ids.has(ev.actor_id)) return true;
                if (ev.target_id && ids.has(ev.target_id)) return true;

                // Проверяем групповые сообщения в этом чате
                if (ev.type === 'chat_group') {
                    try {
                        const metadata = typeof ev.metadata_json === 'string'
                            ? JSON.parse(ev.metadata_json)
                            : ev.metadata_json;
                        if (metadata && String(metadata.group_chat_id) === chatIdStr) {
                            return true;
                        }
                    } catch {
                        // Игнорируем ошибки парсинга
                    }
                }

                return false;
            });

            filtered.sort(
                (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
            );

            if (reset) {
                setAllChatEvents(filtered);
                setDisplayedCount(50);
                setChatEvents(filtered.slice(-50));
            } else {
                setAllChatEvents(filtered);
                setChatEvents(filtered.slice(-displayedCount));
            }
        } catch (err) {
            console.error('Ошибка при загрузке сообщений чата', err);
        }
    };

    const loadMoreMessages = useCallback(() => {
        if (loadingMore || displayedCount >= allChatEvents.length) return;

        setLoadingMore(true);
        const newCount = Math.min(displayedCount + 50, allChatEvents.length);
        setDisplayedCount(newCount);
        setChatEvents(allChatEvents.slice(-newCount));
        setLoadingMore(false);
    }, [allChatEvents, displayedCount, loadingMore]);

    // Intersection Observer для автоматической подгрузки при скролле вверх
    useEffect(() => {
        if (!loadMoreTriggerRef.current) return;

        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting && !loadingMore && displayedCount < allChatEvents.length) {
                    loadMoreMessages();
                }
            },
            {threshold: 0.1}
        );

        observer.observe(loadMoreTriggerRef.current);

        return () => observer.disconnect();
    }, [loadMoreMessages, loadingMore, displayedCount, allChatEvents.length]);

    // Автоматический скролл вниз при открытии чата или новых сообщениях
    const scrollToBottom = useCallback(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({behavior: 'smooth', block: 'end'});
        }
    }, []);

    useEffect(() => {
        if (selectedChat) {
            loadChatEvents(selectedChat, true);
        } else {
            setChatEvents([]);
            setAllChatEvents([]);
            setDisplayedCount(50);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedChat]);

    // Скролл вниз при загрузке сообщений или отправке нового
    useEffect(() => {
        if (chatEvents.length > 0) {
            setTimeout(scrollToBottom, 100);
        }
    }, [chatEvents.length, scrollToBottom]);

    // WebSocket подписка на новые события + периодическая подгрузка
    useEffect(() => {
        if (!selectedChat) return;

        const chatIdStr = String(selectedChat.id);
        const ids = new Set(selectedChat.agent_ids || []);

        // WebSocket подписка
        const ws = connectEventStream((payload) => {
            if (payload.type === 'event_created' && payload.data) {
                const event = payload.data;

                // Проверяем, относится ли событие к текущему чату
                const isRelevant =
                    (event.actor_id && ids.has(event.actor_id)) ||
                    (event.target_id && ids.has(event.target_id)) ||
                    (event.type === 'chat_group' && event.metadata_json &&
                        (() => {
                            try {
                                const metadata = typeof event.metadata_json === 'string'
                                    ? JSON.parse(event.metadata_json)
                                    : event.metadata_json;
                                return metadata && String(metadata.group_chat_id) === chatIdStr;
                            } catch {
                                return false;
                            }
                        })());

                if (isRelevant) {
                    // Перезагружаем события чата
                    loadChatEvents(selectedChat, false);
                }
            }
        });

        // Периодическая подгрузка сообщений (как в EventStream)
        const intervalId = setInterval(() => {
            loadChatEvents(selectedChat, false);
        }, 2000); // Обновляем каждые 2 секунды

        return () => {
            ws.close();
            clearInterval(intervalId);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedChat?.id]);

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
            // Небольшая задержка перед перезагрузкой, чтобы сервер успел обработать
            setTimeout(async () => {
                if (selectedChat) {
                    await loadChatEvents(selectedChat, false);
                }
            }, 300);
        } catch (err) {
            setError('Ошибка при отправке сообщения в чат');
            console.error(err);
        } finally {
            setSending(false);
        }
    };


    return (
        <div className="stack page-container">
            <div className="flex-between">
                <h2 className="panel-title" style={{margin: 0}}>Групповые чаты</h2>
                <button
                    className="btn primary"
                    onClick={() => {
                        const next = !showCreateForm;
                        setShowCreateForm(next);
                        if (next) {
                            // Refresh agents list when opening create form to avoid stale ids
                            fetchAgents(authToken ?? localStorage.getItem('token'));
                        }
                    }}
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
                                    <p className={styles.selectedChatDescription}>
                                        {selectedChat.description}
                                    </p>
                                </div>
                            )}

                            <div className={styles.selectedChatAgents}>
                                <h3>Участники чата ({selectedChat.agent_ids.length})</h3>
                                <div className={styles.agentsGrid}>
                                    {selectedChat.agent_ids.map((agentId) => {
                                        const agent = agents.find((a) => a.id === agentId);
                                        if (!agent) return null;

                                        const moodColor = agent.mood >= 0.7 ? 'var(--accent-green)' :
                                            agent.mood >= 0.4 ? 'var(--accent-yellow)' :
                                                'var(--accent-red)';
                                        const moodLabel = agent.mood >= 0.7 ? 'радостное' :
                                            agent.mood >= 0.4 ? 'нейтральное' :
                                                'подавленное';

                                        return (
                                            <div key={agentId} className={styles.agentCard}>
                                                <div className={styles.agentCardHeader}>
                                                    <span className={styles.agentName}>{agent.name}</span>
                                                    <span
                                                        className={styles.moodIndicator}
                                                        style={{backgroundColor: moodColor}}
                                                        title={`Настроение: ${moodLabel} (${agent.mood.toFixed(2)})`}
                                                    />
                                                </div>
                                                <div className={styles.agentCardInfo}>
                                                    <span className={styles.agentMood}>
                                                        Настроение: {moodLabel}
                                                    </span>
                                                    <span className={styles.agentEnergy}>
                                                        Энергия: {Math.round(agent.energy ?? 0)}%
                                                    </span>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            <div className={styles.chatMessages}>
                                <h3>Сообщения {chatEvents.length > 0 && `(${chatEvents.length}${allChatEvents.length > displayedCount ? ` из ${allChatEvents.length}` : ''})`}</h3>
                                <div
                                    className={styles.messagesList}
                                    ref={messagesContainerRef}
                                >
                                    {chatEvents.length === 0 ? (
                                        <p className={styles.noMessages}>Сообщений пока нет</p>
                                    ) : (
                                        <>
                                            {allChatEvents.length > displayedCount && (
                                                <div ref={loadMoreTriggerRef} className={styles.loadMoreTrigger}>
                                                    {loadingMore ? (
                                                        <span className={styles.loadingText}>Загрузка...</span>
                                                    ) : (
                                                        <button
                                                            className={styles.loadMoreButton}
                                                            onClick={loadMoreMessages}
                                                        >
                                                            Загрузить еще ({allChatEvents.length - displayedCount})
                                                        </button>
                                                    )}
                                                </div>
                                            )}
                                            <ul>
                                                {chatEvents.map((event) => {
                                                    const agent = event.actor_id
                                                        ? agents.find((a) => a.id === event.actor_id)
                                                        : null;

                                                    return (
                                                        <li key={event.id} className={styles.messageItem}>
                                                            <div className={styles.messageBubble}>
                                                                {agent && (
                                                                    <div className={styles.messageAuthor}>
                                                                        {agent.name}
                                                                    </div>
                                                                )}
                                                                <div className={styles.messageText}>
                                                                    {event.description}
                                                                </div>
                                                                <div className={styles.messageMeta}>
                                                                    <span className={styles.messageTime}>
                                                                        {event.timestamp
                                                                            ? new Date(event.timestamp).toLocaleString('ru-RU', {
                                                                                day: '2-digit',
                                                                                month: '2-digit',
                                                                                hour: '2-digit',
                                                                                minute: '2-digit'
                                                                            })
                                                                            : ''}
                                                                    </span>
                                                                </div>
                                                            </div>
                                                        </li>
                                                    );
                                                })}
                                            </ul>
                                            <div ref={messagesEndRef}/>
                                        </>
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

