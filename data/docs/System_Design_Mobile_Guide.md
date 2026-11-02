# System Design для Android разработчика

## Основные принципы масштабирования

### 1. Вертикальное vs Горизонтальное масштабирование
- **Вертикальное**: увеличение мощности сервера (CPU, RAM)
- **Горизонтальное**: добавление большего количества серверов
- Для мобильных приложений важно понимать, как backend масштабируется

### 2. Load Balancer (Балансировщик нагрузки)
- Распределяет трафик между серверами
- Для мобильного разработчика: понимать, что запросы могут идти на разные серверы
- Важность stateless API для мобильных приложений

### 3. Database Scaling

#### Репликация (Master-Slave)
- Master: запись данных
- Slave: чтение данных
- Мобильное приложение может читать из ближайшей реплики

#### Шардирование (Sharding)
- Разделение данных по разным базам
- Пример: пользователи по географии или по user_id

### 4. Кэширование

#### Уровни кэширования для мобильных приложений:
1. **Client-side cache** (на устройстве)
   - Room Database
   - DataStore
   - In-memory cache (LruCache)

2. **CDN** (Content Delivery Network)
   - Статические ресурсы (изображения, видео)
   - Ближайший к пользователю сервер

3. **Server-side cache**
   - Redis, Memcached
   - Кэширование API ответов

#### Cache Invalidation стратегии:
- **TTL** (Time To Live): данные устаревают через время
- **Write-through**: обновление кэша при записи
- **Write-back**: отложенная запись в БД
- **Cache-aside**: приложение управляет кэшем

### 5. CAP Theorem
- **C**onsistency (Согласованность)
- **A**vailability (Доступность)
- **P**artition Tolerance (Устойчивость к разделению)

Можно выбрать только 2 из 3:
- **CP**: банковские приложения (важна согласованность)
- **AP**: социальные сети (важна доступность)

## Ключевые компоненты системы

### 1. API Gateway
- Единая точка входа для всех API запросов
- Rate limiting
- Authentication/Authorization
- Request routing

Для мобильного разработчика:
- Понимание версионирования API (v1, v2)
- Обработка rate limit ошибок (429)

### 2. Message Queue (Очереди сообщений)
- Асинхронная обработка задач
- Примеры: RabbitMQ, Kafka, AWS SQS

Применение в мобильной разработке:
- Push-уведомления
- Обработка загрузки файлов
- Аналитика событий

### 3. WebSocket vs Polling
- **Short Polling**: периодические запросы
- **Long Polling**: держит соединение открытым
- **WebSocket**: двусторонняя связь в реальном времени

Для Android:
- WebSocket для чатов, live updates
- Server-Sent Events (SSE) для односторонних обновлений

## Проектирование мобильных систем

### 1. Offline-First архитектура
```
User Action → Local DB → Sync Queue → Backend
              ↓
         Immediate UI Update
```

Ключевые моменты:
- Локальное хранилище как источник истины
- Синхронизация в фоне
- Conflict resolution при синхронизации

### 2. Pagination
- **Offset-based**: `?page=2&limit=20`
  - Проблема: пропуск элементов при добавлении новых
- **Cursor-based**: `?cursor=abc123&limit=20`
  - Более надежно для real-time данных

### 3. Rate Limiting на клиенте
- Debouncing для поиска
- Throttling для скролла
- Exponential backoff при ошибках

### 4. Retry механизмы
```kotlin
// Exponential backoff
delay = baseDelay * 2.0.pow(attemptNumber)
```

Стратегии:
- Idempotent запросы (можно повторять безопасно)
- Request deduplication (по request_id)

## Специфичные системы для мобильных приложений

### 1. Push Notification System

Компоненты:
- **Provider**: FCM (Firebase Cloud Messaging), APNs
- **Topic-based**: подписка на темы
- **Token-based**: индивидуальные уведомления

Архитектура:
```
Backend → FCM/APNs → Device
Device → Register Token → Backend DB
```

### 2. Image/Video Upload System

Оптимизации:
- **Compression** на клиенте
- **Chunked upload** для больших файлов
- **Presigned URLs** (S3) для прямой загрузки
- **Background upload** с WorkManager

### 3. News Feed System

Компоненты:
- **Fan-out on write**: предварительная генерация ленты
- **Fan-out on read**: генерация при запросе
- **Hybrid**: для популярных пользователей - on read

Для мобильного приложения:
- Prefetching следующей страницы
- Кэширование ленты локально
- Incremental updates (только новые посты)

### 4. Chat System

Архитектура:
```
Client ←→ WebSocket Server ←→ Message Queue ←→ Message Service
                                                      ↓
                                              Message Storage
```

Ключевые фичи:
- Message delivery status (sent, delivered, read)
- Offline message queue
- End-to-end encryption
- Media message handling

### 5. Location-based Services

Компоненты:
- **Geohashing**: кодирование координат
- **QuadTree/R-Tree**: пространственные индексы
- **Redis Geo**: встроенная поддержка геоданных

Для Android:
- Батарейно-эффективное отслеживание локации
- Geofencing
- Кэширование близлежащих объектов

## Метрики и мониторинг

### Ключевые метрики для мобильных приложений:

1. **Performance**
   - App startup time
   - Screen rendering time (60 FPS)
   - API response time
   - Memory usage

2. **Reliability**
   - Crash rate
   - ANR (Application Not Responding) rate
   - Success rate API calls

3. **Network**
   - Bandwidth usage
   - Request count
   - Failed requests ratio

4. **Business**
   - DAU/MAU (Daily/Monthly Active Users)
   - Session length
   - Retention rate

### Инструменты:
- Firebase Crashlytics
- Firebase Performance Monitoring
- Custom analytics events

## Безопасность

### 1. Authentication
- **OAuth 2.0**: стандарт для авторизации
- **JWT** (JSON Web Token): токены доступа
- **Refresh Token**: обновление access token

Хранение на Android:
- EncryptedSharedPreferences для токенов
- Keystore для криптографических ключей

### 2. API Security
- **HTTPS**: обязательно для всех запросов
- **Certificate Pinning**: защита от MITM атак
- **API Key rotation**: регулярная смена ключей
- **Request signing**: подпись запросов

### 3. Data Protection
- Шифрование локальных данных
- Обфускация кода (ProGuard/R8)
- Root/Jailbreak detection

## Оценка масштаба (Back-of-envelope estimation)

### Пример: Instagram-like приложение

**Дано:**
- 500M DAU (Daily Active Users)
- Каждый пользователь загружает 2 фото в день
- Средний размер фото: 2MB

**Расчеты:**

1. **Storage per day:**
   - 500M × 2 photos × 2MB = 2PB/day

2. **QPS (Queries Per Second):**
   - 500M users × 100 requests/day = 50B requests/day
   - 50B / 86400 seconds ≈ 580K QPS
   - Peak QPS ≈ 2 × 580K = 1.16M QPS

3. **Bandwidth:**
   - Upload: 2PB/day ÷ 86400 = 23GB/s
   - Read:Write ratio = 100:1
   - Download: 2.3TB/s

### Полезные числа для оценок:

- **Latency:**
  - Memory: 100ns
  - SSD: 100μs
  - Network (same datacenter): 500μs
  - Network (cross-continent): 150ms

- **Throughput:**
  - SSD: 1GB/s
  - Network: 1Gbps (125MB/s)

- **Storage:**
  - 1 char = 1 byte
  - 1 UUID = 16 bytes
  - 1 timestamp = 8 bytes

## Паттерны для мобильной разработки

### 1. Repository Pattern
```kotlin
interface Repository {
    suspend fun getData(): Flow<Result<Data>>
}

class RepositoryImpl(
    private val remoteDataSource: RemoteDataSource,
    private val localDataSource: LocalDataSource
) : Repository {
    override suspend fun getData() = flow {
        // Emit cached data first
        emit(localDataSource.getData())
        
        // Fetch from network
        val result = remoteDataSource.getData()
        if (result.isSuccess) {
            localDataSource.saveData(result.data)
            emit(result)
        }
    }
}
```

### 2. Single Source of Truth
- Локальная БД как единственный источник данных
- UI подписывается только на локальные данные
- Network обновляет локальную БД

### 3. Optimistic Updates
```kotlin
fun likePost(postId: String) {
    // 1. Update UI immediately
    updateLocalPost(postId, liked = true)
    
    // 2. Send to server
    scope.launch {
        try {
            api.likePost(postId)
        } catch (e: Exception) {
            // 3. Rollback on error
            updateLocalPost(postId, liked = false)
        }
    }
}
```

## Типичные вопросы на собеседовании

### 1. "Спроектируй Instagram"

**Ключевые компоненты:**
- User Service (регистрация, профили)
- Post Service (создание, хранение постов)
- Feed Service (генерация ленты)
- Follow Service (подписки)
- Like/Comment Service
- Notification Service
- Media Storage (S3, CDN)

**Мобильная специфика:**
- Offline создание постов
- Image compression перед загрузкой
- Infinite scroll с pagination
- Prefetching изображений
- Local cache стратегия

### 2. "Спроектируй мессенджер"

**Компоненты:**
- WebSocket для real-time
- Message Queue для доставки
- Message Storage (NoSQL для масштабируемости)
- Media Service для файлов
- Presence Service (online/offline статус)

**Мобильная специфика:**
- Offline message queue
- Message sync при подключении
- Push notifications для новых сообщений
- Local encryption
- Typing indicators

### 3. "Спроектируй Uber"

**Компоненты:**
- Location Service (отслеживание водителей)
- Matching Service (водитель-пассажир)
- Trip Service (управление поездками)
- Payment Service
- Notification Service
- Map Service

**Мобильная специфика:**
- Battery-efficient location tracking
- Real-time location updates (WebSocket)
- Offline map caching
- Route optimization
- ETA calculation

## Чек-лист для System Design интервью

### Шаг 1: Уточнение требований (3-5 мин)
- [ ] Функциональные требования
- [ ] Нефункциональные требования (масштаб, производительность)
- [ ] Платформы (iOS, Android, Web)
- [ ] Offline поддержка?

### Шаг 2: High-level дизайн (10-15 мин)
- [ ] Основные компоненты системы
- [ ] API endpoints
- [ ] Data models
- [ ] Диаграмма архитектуры

### Шаг 3: Deep dive (15-20 мин)
- [ ] Database schema
- [ ] Кэширование стратегия
- [ ] Масштабирование
- [ ] Обработка edge cases

### Шаг 4: Wrap up (5 мин)
- [ ] Bottlenecks
- [ ] Trade-offs
- [ ] Monitoring
- [ ] Будущие улучшения

## Полезные ресурсы

- System Design Interview Vol 1 & 2 - Alex Xu
- Designing Data-Intensive Applications - Martin Kleppmann
- Android Architecture Components
- Firebase Documentation
- AWS Mobile Services
