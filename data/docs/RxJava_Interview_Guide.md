# RxJava Interview Guide

## Что это?

**RxJava (ReactiveX for Java)** — библиотека для реактивного программирования с использованием observable sequences (наблюдаемых последовательностей).

### Основные концепции:
- **Observable** — источник данных, который эмитит элементы
- **Observer** — подписчик, который реагирует на эмитированные элементы
- **Operators** — функции для трансформации, фильтрации и комбинирования потоков данных
- **Schedulers** — управление потоками выполнения (threading)

### Типы Observable:
- **Observable** — может эмитить 0..N элементов
- **Single** — эмитит ровно 1 элемент или ошибку
- **Maybe** — эмитит 0 или 1 элемент
- **Completable** — не эмитит данные, только сигнал завершения или ошибку
- **Flowable** — Observable с поддержкой backpressure

---

## Какие проблемы решает?

### 1. **Асинхронное программирование**
Упрощает работу с асинхронными операциями без callback hell:
```kotlin
// До RxJava (callback hell)
api.getUser(userId, object : Callback {
    override fun onSuccess(user: User) {
        api.getPosts(user.id, object : Callback {
            override fun onSuccess(posts: List<Post>) {
                // ...
            }
        })
    }
})

// С RxJava
api.getUser(userId)
    .flatMap { user -> api.getPosts(user.id) }
    .subscribe { posts -> /* ... */ }
```

### 2. **Управление потоками (Threading)**
Простое переключение между потоками:
```kotlin
observable
    .subscribeOn(Schedulers.io())        // выполнение в IO потоке
    .observeOn(AndroidSchedulers.mainThread()) // результат в UI потоке
    .subscribe { result -> updateUI(result) }
```

### 3. **Композиция асинхронных операций**
Объединение нескольких источников данных:
```kotlin
Observable.zip(
    api.getUser(userId),
    api.getUserSettings(userId),
    api.getUserPosts(userId)
) { user, settings, posts ->
    UserProfile(user, settings, posts)
}.subscribe { profile -> /* ... */ }
```

### 4. **Обработка ошибок**
Централизованная обработка ошибок в цепочке:
```kotlin
observable
    .retry(3)                    // повтор при ошибке
    .onErrorReturn { defaultValue } // значение по умолчанию
    .subscribe(
        { result -> /* success */ },
        { error -> /* handle error */ }
    )
```

### 5. **Debounce, Throttle для UI событий**
Оптимизация обработки пользовательского ввода:
```kotlin
searchEditText.textChanges()
    .debounce(300, TimeUnit.MILLISECONDS) // ждем 300мс после последнего ввода
    .filter { it.length >= 3 }
    .switchMap { query -> api.search(query) }
    .subscribe { results -> showResults(results) }
```

---

## Недостатки и проблемы

### 1. **Обязательная отписка (Memory Leaks)**
**КРИТИЧНО:** Необходимо отписываться при уничтожении компонента, иначе утечки памяти!

```kotlin
class MyActivity : AppCompatActivity() {
    private val compositeDisposable = CompositeDisposable()
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        val disposable = api.getData()
            .subscribeOn(Schedulers.io())
            .observeOn(AndroidSchedulers.mainThread())
            .subscribe { data -> updateUI(data) }
        
        compositeDisposable.add(disposable) // добавляем в контейнер
    }
    
    override fun onDestroy() {
        compositeDisposable.clear() // ОБЯЗАТЕЛЬНО отписываемся!
        super.onDestroy()
    }
}
```

**Альтернативы для управления подписками:**
```kotlin
// 1. CompositeDisposable
private val disposables = CompositeDisposable()
disposables.add(observable.subscribe())
disposables.clear() // в onDestroy

// 2. Одиночная подписка
private var disposable: Disposable? = null
disposable = observable.subscribe()
disposable?.dispose() // в onDestroy

// 3. RxLifecycle (библиотека)
observable
    .compose(bindToLifecycle())
    .subscribe()

// 4. AutoDispose (библиотека)
observable
    .autoDispose(scope)
    .subscribe()
```

### 2. **Крутая кривая обучения**
- Множество операторов (100+)
- Сложность понимания для новичков
- Трудно дебажить цепочки операторов

### 3. **Backpressure проблемы**
Когда producer эмитит данные быстрее, чем consumer их обрабатывает:
```kotlin
// Решение: использовать Flowable вместо Observable
Flowable.create({ emitter ->
    // emit data
}, BackpressureStrategy.BUFFER) // или DROP, LATEST, ERROR
```

### 4. **Размер библиотеки**
- Увеличивает размер APK
- Много методов (может потребоваться multidex)

### 5. **Производительность**
- Overhead при создании множества объектов
- Не всегда оправдано для простых операций

---

## Примеры использования

### 1. **Network запросы (Retrofit + RxJava)**
```kotlin
interface ApiService {
    @GET("users/{id}")
    fun getUser(@Path("id") userId: String): Single<User>
    
    @GET("posts")
    fun getPosts(): Observable<List<Post>>
}

// Использование
apiService.getUser("123")
    .subscribeOn(Schedulers.io())
    .observeOn(AndroidSchedulers.mainThread())
    .subscribe(
        { user -> showUser(user) },
        { error -> showError(error) }
    )
```

### 2. **Комбинирование запросов**

#### Последовательное выполнение (flatMap)
```kotlin
// Простой пример - только posts в subscribe
apiService.getUser(userId)
    .flatMap { user -> apiService.getUserPosts(user.id) }
    .subscribe { posts -> /* ... */ }

// ✅ Если нужен и user, и posts - используем map внутри flatMap
apiService.getUser(userId)
    .flatMap { user -> 
        apiService.getUserPosts(user.id)
            .map { posts -> Pair(user, posts) } // Комбинируем результаты
    }
    .subscribe { (user, posts) -> 
        // Теперь доступны оба объекта!
        showUser(user)
        showPosts(posts)
    }

// Альтернатива - zipWith
apiService.getUser(userId)
    .flatMap { user ->
        apiService.getUserPosts(user.id)
            .zipWith(Single.just(user)) { posts, u -> 
                UserWithPosts(u, posts) 
            }
    }
    .subscribe { userWithPosts -> /* ... */ }
```

#### Параллельное выполнение (zip)
```kotlin
Single.zip(
    apiService.getUser(userId),
    apiService.getUserSettings(userId)
) { user, settings -> Pair(user, settings) }
    .subscribe { (user, settings) -> /* ... */ }
```

#### Почему нет subscribeOn/observeOn в примере?
```kotlin
// В упрощенном примере их опустили для краткости
// В реальном коде они ОБЯЗАТЕЛЬНЫ:

apiService.getUser(userId)
    .subscribeOn(Schedulers.io())           // Где выполняется запрос
    .flatMap { user -> 
        apiService.getUserPosts(user.id)    // Выполнится тоже в IO
            .map { posts -> Pair(user, posts) }
    }
    .observeOn(AndroidSchedulers.mainThread()) // Где обрабатывается результат
    .subscribe { (user, posts) -> 
        updateUI(user, posts) // Выполнится в UI потоке
    }

// Важно:
// - subscribeOn определяет поток для ВСЕЙ цепочки выше subscribe
// - observeOn переключает поток для операторов НИЖЕ него
// - Обычно достаточно одного subscribeOn в начале
```

#### Тот же запрос на Kotlin Coroutines + Retrofit
```kotlin
// 1. Определение API (Retrofit с корутинами)
interface ApiService {
    @GET("users/{id}")
    suspend fun getUser(@Path("id") userId: String): User
    
    @GET("users/{id}/posts")
    suspend fun getUserPosts(@Path("id") userId: String): List<Post>
}

// 2. Использование в ViewModel
class MyViewModel : ViewModel() {
    fun loadUserWithPosts(userId: String) {
        viewModelScope.launch {
            try {
                // ✅ Последовательное выполнение - просто вызываем по порядку
                val user = apiService.getUser(userId)      // suspend функция
                val posts = apiService.getUserPosts(user.id) // suspend функция
                
                // Оба объекта доступны!
                _uiState.value = Success(user, posts)
                
            } catch (e: Exception) {
                _uiState.value = Error(e)
            }
        }
    }
}

// 3. Если нужно явно указать Dispatcher (аналог subscribeOn)
viewModelScope.launch {
    try {
        val user = withContext(Dispatchers.IO) {
            apiService.getUser(userId) // Выполнится в IO потоке
        }
        
        val posts = withContext(Dispatchers.IO) {
            apiService.getUserPosts(user.id)
        }
        
        // Автоматически вернулись в Main поток (viewModelScope = Main)
        updateUI(user, posts) // Выполнится в UI потоке
        
    } catch (e: Exception) {
        handleError(e)
    }
}

// 4. Параллельное выполнение (аналог zip)
viewModelScope.launch {
    try {
        val userDeferred = async { apiService.getUser(userId) }
        val settingsDeferred = async { apiService.getUserSettings(userId) }
        
        // Ждем оба результата параллельно
        val user = userDeferred.await()
        val settings = settingsDeferred.await()
        
        _uiState.value = Success(user, settings)
    } catch (e: Exception) {
        _uiState.value = Error(e)
    }
}
```

#### Сравнение RxJava vs Coroutines для цепочки запросов

```kotlin
// ════════════════════════════════════════════════════════════════
// RxJava - более многословно
// ════════════════════════════════════════════════════════════════
private val compositeDisposable = CompositeDisposable()

fun loadData() {
    val disposable = apiService.getUser(userId)
        .subscribeOn(Schedulers.io())
        .flatMap { user ->
            apiService.getUserPosts(user.id)
                .map { posts -> Pair(user, posts) }
        }
        .observeOn(AndroidSchedulers.mainThread())
        .subscribe(
            { (user, posts) -> 
                updateUI(user, posts)
            },
            { error -> 
                handleError(error)
            }
        )
    
    compositeDisposable.add(disposable)
}

override fun onDestroy() {
    compositeDisposable.clear() // ОБЯЗАТЕЛЬНО!
    super.onDestroy()
}

// ════════════════════════════════════════════════════════════════
// Coroutines - проще и читабельнее
// ════════════════════════════════════════════════════════════════
fun loadData() {
    viewModelScope.launch {
        try {
            val user = apiService.getUser(userId)
            val posts = apiService.getUserPosts(user.id)
            
            updateUI(user, posts)
        } catch (e: Exception) {
            handleError(e)
        }
    }
    // Отписка автоматическая при уничтожении ViewModel!
}
```

### 3. **Работа с БД (Room + RxJava)**
```kotlin
@Dao
interface UserDao {
    @Query("SELECT * FROM users")
    fun getAllUsers(): Flowable<List<User>>
    
    @Insert
    fun insertUser(user: User): Completable
}

// Использование
userDao.getAllUsers()
    .subscribeOn(Schedulers.io())
    .observeOn(AndroidSchedulers.mainThread())
    .subscribe { users -> updateUI(users) }
```

### 4. **Поиск с debounce**
```kotlin
// RxBinding для EditText
RxTextView.textChanges(searchEditText)
    .debounce(300, TimeUnit.MILLISECONDS)
    .filter { it.length >= 3 }
    .distinctUntilChanged()
    .switchMap { query -> 
        apiService.search(query.toString())
            .onErrorReturn { emptyList() }
    }
    .subscribeOn(Schedulers.io())
    .observeOn(AndroidSchedulers.mainThread())
    .subscribe { results -> showResults(results) }
```

### 5. **Polling (периодические запросы)**
```kotlin
Observable.interval(5, TimeUnit.SECONDS)
    .flatMap { apiService.getUpdates() }
    .subscribeOn(Schedulers.io())
    .observeOn(AndroidSchedulers.mainThread())
    .subscribe { updates -> processUpdates(updates) }
```

### 6. **Кэширование**
```kotlin
val cachedObservable = apiService.getData()
    .subscribeOn(Schedulers.io())
    .cache() // кэширует результат

// Все подписчики получат закэшированный результат
cachedObservable.subscribe { /* ... */ }
cachedObservable.subscribe { /* ... */ }
```

### 7. **Обработка кликов с защитой от двойного клика**
```kotlin
RxView.clicks(button)
    .throttleFirst(1, TimeUnit.SECONDS) // игнорирует клики в течение 1 сек
    .subscribe { performAction() }
```

---

## Популярные операторы

### Создание:
- `just()` — создает Observable из значения
- `fromIterable()` — из коллекции
- `create()` — кастомное создание
- `defer()` — отложенное создание

### Трансформация:
- `map()` — преобразование каждого элемента
- `flatMap()` — преобразование в Observable и объединение
- `switchMap()` — отменяет предыдущий Observable при новом событии
- `concatMap()` — последовательное выполнение

### Фильтрация:
- `filter()` — фильтрация по условию
- `take()` — берет первые N элементов
- `skip()` — пропускает первые N элементов
- `distinct()` — убирает дубликаты
- `debounce()` — эмитит элемент после паузы
- `throttleFirst()` — эмитит первый элемент в окне времени

### Комбинирование:
- `zip()` — объединяет несколько Observable
- `merge()` — объединяет потоки в один
- `concat()` — последовательное объединение
- `combineLatest()` — комбинирует последние значения

### Обработка ошибок:
- `onErrorReturn()` — возвращает значение при ошибке
- `onErrorResumeNext()` — переключается на другой Observable
- `retry()` — повторяет при ошибке

### Schedulers:
- `Schedulers.io()` — для IO операций (сеть, БД)
- `Schedulers.computation()` — для вычислений
- `Schedulers.newThread()` — новый поток для каждой задачи
- `AndroidSchedulers.mainThread()` — UI поток Android

---

## RxJava vs Coroutines (для сравнения)

| Аспект | RxJava | Kotlin Coroutines |
|--------|--------|-------------------|
| **Кривая обучения** | Сложная | Проще |
| **Backpressure** | Есть (Flowable) | Есть (Flow) |
| **Отмена** | Disposable | Job/CoroutineScope |
| **Размер библиотеки** | Большой | Встроено в Kotlin |
| **Streams** | Горячие и холодные | Холодные (Flow) |
| **Операторы** | 100+ | Меньше, но достаточно |

---

## Типичные вопросы на собеседовании

1. **В чем разница между `flatMap`, `switchMap` и `concatMap`?**
   - `flatMap` — выполняет параллельно, порядок не гарантирован
   - `switchMap` — отменяет предыдущий при новом событии
   - `concatMap` — выполняет последовательно, сохраняет порядок

2. **Что такое backpressure и как его обрабатывать?**
   - Ситуация, когда producer быстрее consumer
   - Решение: Flowable с BackpressureStrategy (BUFFER, DROP, LATEST, ERROR)

3. **Как избежать утечек памяти?**
   - Использовать CompositeDisposable
   - Отписываться в onDestroy/onStop
   - Использовать RxLifecycle или AutoDispose

4. **В чем разница между Observable и Flowable?**
   - Flowable поддерживает backpressure
   - Observable проще и быстрее для небольших потоков

5. **Что такое Hot и Cold Observable?**
   - **Cold** — начинает эмитить при подписке (network запросы)
   - **Hot** — эмитит независимо от подписчиков (UI события)

6. **Когда использовать `subscribeOn` vs `observeOn`?**
   - `subscribeOn` — где выполняется источник данных
   - `observeOn` — где обрабатывается результат

---

## Почему перешли на Coroutines?

- Проще синтаксис (императивный стиль)
- Встроено в Kotlin (нет зависимостей)
- Лучше интеграция с Android (ViewModel, Lifecycle)
- Меньше boilerplate кода
- Structured concurrency из коробки
