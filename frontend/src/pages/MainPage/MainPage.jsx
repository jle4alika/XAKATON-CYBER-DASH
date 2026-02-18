import React from 'react';
import styles from './MainPage.module.css';
import {Link} from "react-router-dom";
import logo from '../../../assets/gloomth logo without background.png';

const MainPage = () => {
    return (
        <div className={styles.page}>
            {/* Hero Section */}
            <section className={styles.hero}>
                <div className={styles.container}>
                    <div className={styles.heroContent}>
                        <div className={styles.heroText}>
                            <h1 className={styles.heroTitle}>
                                <span className={styles.heroTitleLight}>КИБЕР-РЫВОК</span>
                            </h1>
                            <p className={styles.heroSubtitle}>
                                симулятор живых существ с памятью, эмоциями и веб-интерфейсом
                            </p>

                            <div className={styles.heroTags}>
                                <span className={styles.tag}>Разные агенты ИИ</span>
                                <span className={styles.tag}>Настраиваемые тематики общения агентов</span>
                                <span className={styles.tag}>Создание агентов</span>
                                <span className={styles.tag}>Настройка поведения агентов</span>
                            </div>


                            <Link to="/register"
                                  className={styles.heroCta}
                                  aria-label="На главную">
                                Попробовать сейчас
                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                                    <path d="M4 10H16M16 10L11 5M16 10L11 15" stroke="#1a1a1a" strokeWidth="2.5"
                                          strokeLinecap="round" strokeLinejoin="round"/>
                                </svg>
                            </Link>

                        </div>

                        <div className={styles.heroVisual}>
                            <div className={styles.sunIcon}>
                                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                                    <circle cx="24" cy="24" r="8" fill="#84cc16"/>
                                    <path
                                        d="M24 4V10M24 38V44M44 24H38M10 24H4M37.66 10.34L33.42 14.58M14.58 33.42L10.34 37.66M37.66 37.66L33.42 33.42M14.58 14.58L10.34 10.34"
                                        stroke="#84cc16" strokeWidth="3" strokeLinecap="round"/>
                                </svg>
                            </div>

                            <div className={styles.brainChip}>
                                <div className={styles.chipBase}>
                                    <div className={styles.chipPins}>
                                        {[...Array(8)].map((_, i) => (
                                            <div key={i} className={styles.pin} style={{left: `${10 + i * 12}%`}}/>
                                        ))}
                                        {[...Array(8)].map((_, i) => (
                                            <div key={i} className={`${styles.pin} ${styles.pinRight}`}
                                                 style={{right: `${10 + i * 12}%`}}/>
                                        ))}
                                        {[...Array(6)].map((_, i) => (
                                            <div key={i} className={`${styles.pin} ${styles.pinBottom}`}
                                                 style={{bottom: `${10 + i * 14}%`, left: 'auto', right: 'auto'}}/>
                                        ))}
                                    </div>
                                    <div className={styles.chipBody}>
                                        <div className={styles.brainGlow}/>
                                        <img className={styles.brand} src={logo}/>
                                    </div>
                                </div>
                            </div>

                            <div className={styles.sunIconSmall}>
                                <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                                    <circle cx="16" cy="16" r="5" fill="#22d3ee"/>
                                    <path
                                        d="M16 3V7M16 25V29M29 16H25M7 16H3M24.66 7.34L21.83 10.17M10.17 21.83L7.34 24.66M24.66 24.66L21.83 21.83M10.17 10.17L7.34 7.34"
                                        stroke="#22d3ee" strokeWidth="2" strokeLinecap="round"/>
                                </svg>
                            </div>
                        </div>
                    </div>

                    {/* Partners - Технологии */}
                    <div className={styles.partners}>
                        <div className={styles.partnerLogo}>OpenAI API</div>
                        <div className={styles.partnerLogo}>Google Gemini</div>
                        <div className={styles.partnerLogo}>Yandex GPT</div>
                        <div className={styles.partnerLogo}>LangChain</div>
                        <div className={styles.partnerLogo}>Pinecone</div>
                        <div className={styles.partnerLogo}>ChromaDB</div>
                        <div className={styles.partnerLogo}>FastAPI</div>
                        <div className={styles.partnerLogo}>React</div>
                    </div>
                </div>
            </section>

            {/* Services Section */}
            <section className={styles.services} id="services">
                <div className={styles.container}>
                    <h2 className={styles.sectionTitle}>Наши услуги</h2>

                    <div className={styles.servicesGrid}>
                        <div className={`${styles.serviceCard} ${styles.cardCyan}`}>
                            <h3>Сохранение результатов чатов</h3>
                            <p>Векторная база данных для хранения эпизодической памяти агентов. Автоматическая
                                суммаризация старых воспоминаний при переполнении контекста. Агенты помнят прошлые
                                диалоги и используют их для принятия решений.</p>
                        </div>

                        <div className={`${styles.serviceCard} ${styles.cardDark} ${styles.hasImage}`}>
                            <h3>Построение графов отношений</h3>
                            <p>Интерактивный граф, где узлы — агенты, рёбра — отношения. Цвет ребра меняется от уровня
                                симпатии. Формирование долгосрочных отношений (симпатия/антипатия) между агентами на
                                основе их взаимодействий.</p>
                            <div className={styles.cardImage}>
                                <div className={styles.chipIcon}>
                                    <div className={styles.chipIconBody}/>
                                    <img src="../../assets/6d1322e16e7ab94d7f9d2d1a60969270.png"></img>
                                    <div className={styles.chipIconPins}/>
                                </div>
                            </div>
                        </div>

                        <div className={`${styles.serviceCard} ${styles.cardLime}`}>
                            <h3>Готовые ИИ модели</h3>
                            <p>LLM-ядро (OpenAPI/Gemini/Yandex GPT) с моделью настроения. Эмоциональный интеллект:
                                изменение эмоций в зависимости от событий. Смена настроения влияет на стиль речи
                                агента.</p>
                        </div>

                        <div className={`${styles.serviceCard} ${styles.cardLimeWide} ${styles.hasImage}`}>
                            <h3>Отслеживание в реальном времени</h3>
                            <p>Лента событий в реальном времени. Аватары, имена, текущее настроение (иконка/цвет).
                                Дашборд «Жизнь агентов» с полной информацией о состоянии каждого персонажа виртуального
                                мира.</p>
                            <div className={styles.cardImage}>
                                <div className={styles.chipIcon}>
                                    <div className={styles.chipIconBody}/>
                                    <img src="../../assets/6d1322e16e7ab94d7f9d2d1a60969270.png"></img>
                                    <div className={styles.chipIconPins}/>
                                </div>
                            </div>
                        </div>


                    </div>
                </div>
            </section>

            {/* Advantages Section */}
            <section className={styles.advantages} id="advantages">
                <div className={styles.container}>
                    <h2 className={styles.sectionTitle}>Преимущества</h2>

                    <div className={styles.stats}>
                        <div className={styles.stat}>
                            <div className={styles.statNumber}>5+</div>
                            <div className={styles.statLabel}>агентов в симуляции</div>
                        </div>
                        <div className={styles.stat}>
                            <div className={styles.statNumber}>1000+</div>
                            <div className={styles.statLabel}>воспоминаний в векторной БД</div>
                        </div>
                        <div className={styles.stat}>
                            <div className={styles.statNumber}>∞</div>
                            <div className={styles.statLabel}>возможных сценариев</div>
                        </div>
                    </div>

                    <div className={styles.featuresGrid}>
                        <div className={styles.featureCard}>
                            <div className={styles.featureIcon}>
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#84cc16"
                                     strokeWidth="2">
                                    <path
                                        d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                                    <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                                    <line x1="12" y1="22.08" x2="12" y2="12"/>
                                </svg>
                            </div>
                            <div className={styles.featureText}>
                                <h4>Векторная память агентов</h4>
                            </div>
                        </div>

                        <div className={styles.featureCard}>
                            <div className={styles.featureIcon}>
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#84cc16"
                                     strokeWidth="2">
                                    <circle cx="12" cy="12" r="10"/>
                                    <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
                                    <line x1="9" y1="9" x2="9.01" y2="9"/>
                                    <line x1="15" y1="9" x2="15.01" y2="9"/>
                                </svg>
                            </div>
                            <div className={styles.featureText}>
                                <h4>Эмоциональный интеллект</h4>
                            </div>
                        </div>

                        <div className={styles.featureCard}>
                            <div className={styles.featureIcon}>
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#84cc16"
                                     strokeWidth="2">
                                    <circle cx="12" cy="12" r="3"/>
                                    <path
                                        d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                                </svg>
                            </div>
                            <div className={styles.featureText}>
                                <h4>Панель управления миром</h4>
                            </div>
                        </div>

                        <div className={styles.featureCard}>
                            <div className={styles.featureIcon}>
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#84cc16"
                                     strokeWidth="2">
                                    <circle cx="18" cy="5" r="3"/>
                                    <circle cx="6" cy="12" r="3"/>
                                    <circle cx="18" cy="19" r="3"/>
                                    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
                                    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
                                </svg>
                            </div>
                            <div className={styles.featureText}>
                                <h4>Граф отношений в реальном времени</h4>
                            </div>
                        </div>

                        <div className={styles.featureCard}>
                            <div className={styles.featureIcon}>
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#84cc16"
                                     strokeWidth="2">
                                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                                </svg>
                            </div>
                            <div className={styles.featureText}>
                                <h4>Лента событий онлайн</h4>
                            </div>
                        </div>
                        <div className={styles.featureCard}>
                            <div className={styles.featureIcon}>
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
                                     fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                     stroke-linejoin="round">
                                    <path
                                        d="M9.828 9.172a4 4 0 1 0 0 5.656a10 10 0 0 0 2.172 -2.828a10 10 0 0 1 2.172 -2.828a4 4 0 1 1 0 5.656a10 10 0 0 1 -2.172 -2.828a10 10 0 0 0 -2.172 -2.828"/>
                                </svg>
                            </div>
                            <div className={styles.featureText}>
                                <h4>Безграничное количество чатов</h4>
                            </div>
                        </div>
                    </div>
                    <Link to="/register"
                          className={styles.heroCta}
                          aria-label="На главную"
                          style={{maxWidth: "290px"}}>
                        Запустить симуляцию
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M4 10H16M16 10L11 5M16 10L11 15" stroke="#1a1a1a" strokeWidth="2.5"
                                  strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                    </Link>
                </div>
            </section>
        </div>
    );
};

export default MainPage;

