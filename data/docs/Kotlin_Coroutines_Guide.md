# Kotlin Coroutines для Android разработчика (Middle/Middle+)

## 1. Основы корутин

### Что такое корутины?
Корутины — это легковесные потоки, которые позволяют писать асинхронный код в синхронном стиле. Они не блокируют поток и могут быть приостановлены и возобновлены.

### Ключевые концепции

#### Suspend функции
```kotlin
suspend fun fetchData(): String {
    delay(1000) // Приостанавливает корутину, но не блокирует поток
    return "Data"
}
```

**Важно:**
- `suspend` функции могут вызываться только из других `suspend` функций или корутин
- Компилятор преобразует их в state machine с Continuation
- Не блокируют поток, освобождают его для других задач

#### Continuation
```kotlin
// Под капотом suspend функция выглядит так:
fun fetchData(continuation: Continuation<String>): Any? {
    // State machine implementation
}
```

### Корутин билдеры

#### launch
```kotlin
// Запускает корутину и возвращает Job (fire-and-forget)
viewModelScope.launch {
    val data = fetchData()
    updateUI(data)
}
```

#### async/await
```kotlin
// Возвращает Deferred<T> для получения результата
val deferred = viewModelScope.async {
    fetchData()
}
val result = deferred.await()

// Параллельное выполнение
suspend fun loadData() {
    val user = async { fetchUser() }
    val posts = async { fetchPosts() }
    
    // Ждем оба результата
    val userData = user.await()
    val postsData = posts.await()
}
```

#### launch vs async - ключевые различия

##### 1. Возвращаемый тип
```kotlin
// launch - возвращает Job
val job: Job = launch {
    // fire-and-forget
}

// async - возвращает Deferred<T>
val deferred: Deferred<String> = async {
    "result"
}
val result = deferred.await()
```

##### 2. Обработка исключений (ВАЖНО!)

**launch - исключение пробрасывается немедленно:**
```kotlin
// ❌ Исключение пробросится СРАЗУ при возникновении
viewModelScope.launch {
    throw Exception("Error in launch")
    // Исключение идет в CoroutineExceptionHandler или падает приложение
}

// Обработка через try-catch внутри
viewModelScope.launch {
    try {
        throw Exception("Error")
    } catch (e: Exception) {
        println("Поймали: $e")
    }
}

// Обработка через CoroutineExceptionHandler
val handler = CoroutineExceptionHandler { _, exception ->
    println("Caught: $exception")
}
viewModelScope.launch(handler) {
    throw Exception("Error")
}
```

**async - исключение пробрасывается при await():**
```kotlin
// ✅ Исключение НЕ пробросится до вызова await()
val deferred = viewModelScope.async {
    throw Exception("Error in async")
    // Исключение "заморожено" внутри Deferred
}

// Программа продолжает работать...
println("Продолжаем работу")

// ❌ Исключение пробросится ЗДЕСЬ
try {
    deferred.await() // Здесь вылетит исключение
} catch (e: Exception) {
    println("Поймали при await: $e")
}
```

##### 3. Сравнение поведения при ошибках

```kotlin
// Пример с launch
fun testLaunch() = runBlocking {
    val job = launch {
        delay(100)
        println("Launch: до ошибки")
        throw Exception("Launch failed")
        println("Launch: после ошибки") // Не выполнится
    }
    
    delay(200)
    println("Основная корутина продолжает")
    // Вывод:
    // Launch: до ошибки
    // Exception in thread "main" Exception: Launch failed
    // (программа упадет, если нет обработчика)
}

// Пример с async
fun testAsync() = runBlocking {
    val deferred = async {
        delay(100)
        println("Async: до ошибки")
        throw Exception("Async failed")
        println("Async: после ошибки") // Не выполнится
    }
    
    delay(200)
    println("Основная корутина продолжает") // ✅ Выполнится!
    
    try {
        deferred.await() // Здесь вылетит исключение
    } catch (e: Exception) {
        println("Поймали: ${e.message}")
    }
    
    // Вывод:
    // Async: до ошибки
    // Основная корутина продолжает
    // Поймали: Async failed
}
```

##### 4. Множественные async и обработка ошибок

```kotlin
suspend fun loadData() = coroutineScope {
    val user = async { fetchUser() }
    val posts = async { 
        delay(100)
        throw Exception("Posts failed")
    }
    val comments = async { fetchComments() }
    
    try {
        val userData = user.await()      // ✅ Успешно
        val postsData = posts.await()    // ❌ Исключение здесь
        val commentsData = comments.await() // Не выполнится
    } catch (e: Exception) {
        println("Ошибка: ${e.message}")
        // Все корутины будут отменены (structured concurrency)
    }
}
```

##### 5. Когда использовать что?

**Используй launch когда:**
```kotlin
// ✅ Не нужен результат (fire-and-forget)
launch {
    sendAnalytics()
    updateCache()
}

// ✅ Обработка ошибок через CoroutineExceptionHandler
val handler = CoroutineExceptionHandler { _, e ->
    logError(e)
}
launch(handler) {
    riskyOperation()
}

// ✅ Побочные эффекты
launch {
    updateUI()
    showNotification()
}
```

**Используй async когда:**
```kotlin
// ✅ Нужен результат
val result = async { 
    calculateSomething() 
}.await()

// ✅ Параллельное выполнение с результатами
val user = async { fetchUser() }
val posts = async { fetchPosts() }
val data = UserData(user.await(), posts.await())

// ✅ Нужен контроль над обработкой ошибок
val deferred = async { riskyOperation() }
try {
    val result = deferred.await()
} catch (e: Exception) {
    handleError(e)
}
```

##### 6. Отмена и иерархия

```kotlin
// launch - отмена через Job
val job = launch {
    repeat(1000) {
        delay(100)
        println(it)
    }
}
job.cancel() // Отменяем

// async - отмена через Deferred (который наследует Job)
val deferred = async {
    repeat(1000) {
        delay(100)
        println(it)
    }
}
deferred.cancel() // Отменяем
```

##### 7. Практический пример: разница в обработке ошибок

```kotlin
class MyViewModel : ViewModel() {
    
    // ❌ Плохо - ошибка упадет в CoroutineExceptionHandler
    fun loadDataBad() {
        viewModelScope.launch {
            val data = repository.getData() // Может бросить исключение
            _uiState.value = UiState.Success(data)
        }
        // Если ошибка - приложение может упасть
    }
    
    // ✅ Хорошо - явная обработка с launch
    fun loadDataGood1() {
        viewModelScope.launch {
            try {
                val data = repository.getData()
                _uiState.value = UiState.Success(data)
            } catch (e: Exception) {
                _uiState.value = UiState.Error(e.message)
            }
        }
    }
    
    // ✅ Хорошо - с async для контроля
    fun loadDataGood2() {
        viewModelScope.launch {
            val deferred = async { repository.getData() }
            try {
                val data = deferred.await()
                _uiState.value = UiState.Success(data)
            } catch (e: Exception) {
                _uiState.value = UiState.Error(e.message)
            }
        }
    }
    
    // ✅ Отлично - параллельная загрузка с обработкой ошибок
    fun loadMultipleData() {
        viewModelScope.launch {
            try {
                val user = async { repository.getUser() }
                val posts = async { repository.getPosts() }
                val comments = async { repository.getComments() }
                
                _uiState.value = UiState.Success(
                    user = user.await(),
                    posts = posts.await(),
                    comments = comments.await()
                )
            } catch (e: Exception) {
                _uiState.value = UiState.Error(e.message)
            }
        }
    }
}
```

##### 8. Важные нюансы

```kotlin
// 1. async без await() - корутина все равно выполняется
val deferred = async {
    println("Выполняется!")
    heavyComputation()
}
// Даже если не вызвать await(), код выполнится

// 2. Ленивый async
val lazyDeferred = async(start = CoroutineStart.LAZY) {
    println("Выполняется только при await()")
    heavyComputation()
}
// Код НЕ выполнится до вызова await() или start()
lazyDeferred.await() // Только здесь начнется выполнение

// 3. Исключение в async без await()
val deferred = async {
    throw Exception("Error")
}
// Если НИКОГДА не вызвать await(), исключение "потеряется"
// Но при отмене scope исключение все равно обработается
```

##### 9. Резюме различий

| Характеристика | launch | async |
|----------------|--------|-------|
| **Возвращает** | Job | Deferred<T> |
| **Результат** | ❌ Нет | ✅ Да (через await) |
| **Исключения** | Пробрасываются сразу | Пробрасываются при await() |
| **Обработка ошибок** | CoroutineExceptionHandler или try-catch | try-catch вокруг await() |
| **Use case** | Fire-and-forget, побочные эффекты | Получение результата, параллелизм |
| **Когда падает** | При возникновении исключения | При вызове await() |

#### runBlocking
```kotlin
// Блокирует текущий поток (использовать только в тестах и main())
fun main() = runBlocking {
    delay(1000)
    println("Done")
}
```

#### withContext
```kotlin
// Переключает контекст выполнения и возвращает результат
suspend fun loadData(): String = withContext(Dispatchers.IO) {
    // Выполняется в IO потоке
    fetchFromNetwork()
}
```

## 2. Dispatchers (Диспетчеры)

### Типы диспетчеров

```kotlin
// Main - UI поток (Android Main Thread)
launch(Dispatchers.Main) {
    updateUI()
}

// IO - для I/O операций (сеть, БД, файлы)
// Пул до 64 потоков
launch(Dispatchers.IO) {
    val data = database.query()
}

// Default - для CPU-интенсивных задач
// Пул размером = количество ядер CPU
launch(Dispatchers.Default) {
    val result = complexCalculation()
}

// Unconfined - не привязан к конкретному потоку (редко используется)
launch(Dispatchers.Unconfined) {
    // Может выполняться в разных потоках
}
```

### Dispatchers.Unconfined - подробно

#### Что это такое?

**Dispatchers.Unconfined** - это специальный диспетчер, который:
- **Не привязан к конкретному потоку**
- **Выполняется в том потоке, где был вызван** (изначально)
- **После suspend возобновляется в том потоке, где завершилась suspend функция**

#### Как работает?

```kotlin
fun main() = runBlocking {
    launch(Dispatchers.Unconfined) {
        println("1. Поток: ${Thread.currentThread().name}")
        // Выполняется в потоке вызывающей корутины (main)
        
        delay(100) // Suspend точка
        
        println("2. Поток: ${Thread.currentThread().name}")
        // Возобновляется в потоке, где завершился delay (kotlinx.coroutines.DefaultExecutor)
        
        withContext(Dispatchers.IO) {
            println("3. Поток: ${Thread.currentThread().name}")
            // IO поток
        }
        
        println("4. Поток: ${Thread.currentThread().name}")
        // Возобновляется в IO потоке (последний использованный)
    }
}

// Вывод:
// 1. Поток: main
// 2. Поток: kotlinx.coroutines.DefaultExecutor
// 3. Поток: DefaultDispatcher-worker-1
// 4. Поток: DefaultDispatcher-worker-1
```

#### Сравнение с другими диспетчерами:

```kotlin
// Main - всегда в Main потоке
launch(Dispatchers.Main) {
    println(Thread.currentThread().name) // main
    delay(100)
    println(Thread.currentThread().name) // main
    withContext(Dispatchers.IO) { }
    println(Thread.currentThread().name) // main (вернулся!)
}

// Unconfined - "прыгает" между потоками
launch(Dispatchers.Unconfined) {
    println(Thread.currentThread().name) // main
    delay(100)
    println(Thread.currentThread().name) // DefaultExecutor
    withContext(Dispatchers.IO) { }
    println(Thread.currentThread().name) // IO поток (остался!)
}
```

#### Зачем он нужен?

**В двух словах:** Для **оптимизации производительности** - избегает лишних переключений потоков.

##### 1. Избегает overhead переключения контекста

```kotlin
// С обычным диспетчером
launch(Dispatchers.Default) {
    // Переключение на Default поток
    val data = fetchData() // suspend функция
    // Переключение обратно на Default поток
    process(data)
    // Переключение на Default поток
}
// Много переключений = overhead

// С Unconfined
launch(Dispatchers.Unconfined) {
    // Выполняется где вызвано
    val data = fetchData() // suspend функция
    // Продолжает в том же потоке, где завершился fetchData
    process(data)
    // Нет лишних переключений!
}
```

##### 2. Для тестирования

```kotlin
// В тестах - выполнение синхронное и предсказуемое
@Test
fun testCoroutine() = runBlocking {
    launch(Dispatchers.Unconfined) {
        // Выполнится немедленно в текущем потоке
        // Без задержек на переключение
    }
}
```

##### 3. Для event loop / callback-based кода

```kotlin
// Когда нужно продолжить в том же потоке, где пришел callback
fun observeData() {
    dataSource.observe { data ->
        // Callback пришел в каком-то потоке
        launch(Dispatchers.Unconfined) {
            // Продолжит в том же потоке callback
            processData(data)
        }
    }
}
```

#### Почему редко используется?

**Проблемы:**

##### 1. Непредсказуемость

```kotlin
launch(Dispatchers.Unconfined) {
    println("Поток 1: ${Thread.currentThread().name}")
    delay(100)
    println("Поток 2: ${Thread.currentThread().name}") // Другой поток!
    updateUI() // ❌ CRASH! Может быть не в Main потоке
}
```

##### 2. Сложность отладки

```kotlin
launch(Dispatchers.Unconfined) {
    // Код "прыгает" между потоками
    // Сложно понять, где что выполняется
    // Сложно воспроизвести баги
}
```

##### 3. Нарушение thread-safety

```kotlin
var counter = 0

launch(Dispatchers.Unconfined) {
    counter++ // Поток A
    delay(1)
    counter++ // Поток B - race condition!
}
```

#### Когда использовать?

**Почти никогда в production коде!** Только для:

```kotlin
// 1. Тесты
@Test
fun test() = runBlocking {
    launch(Dispatchers.Unconfined) {
        // Синхронное выполнение
    }
}

// 2. Библиотеки низкого уровня
// Где важна производительность и контроль над потоками

// 3. Специфичные оптимизации
// Когда точно знаешь что делаешь
```

#### Практический пример - разница в поведении:

```kotlin
fun main() = runBlocking {
    println("=== Main ===")
    launch(Dispatchers.Main) {
        println("Start: ${Thread.currentThread().name}")
        delay(100)
        println("After delay: ${Thread.currentThread().name}")
    }
    
    println("\n=== Unconfined ===")
    launch(Dispatchers.Unconfined) {
        println("Start: ${Thread.currentThread().name}")
        delay(100)
        println("After delay: ${Thread.currentThread().name}")
    }
}

// Вывод:
// === Main ===
// Start: main
// After delay: main (тот же поток!)
//
// === Unconfined ===
// Start: main
// After delay: kotlinx.coroutines.DefaultExecutor (другой поток!)
```

#### Резюме: Dispatchers.Unconfined

**Что это:**
- Не привязан к потоку
- Выполняется где вызван, возобновляется где завершилась suspend функция
- "Прыгает" между потоками

**Зачем придумали:**
- Оптимизация производительности (нет overhead переключения)
- Для тестов (синхронное выполнение)
- Для низкоуровневых библиотек

**Почему редко используется:**
- ❌ Непредсказуемое поведение
- ❌ Сложная отладка
- ❌ Риск race conditions
- ❌ Может крашнуть UI (если не в Main потоке)

**Правило:** Используй **Main**, **IO**, **Default** в 99.9% случаев. Unconfined только если точно знаешь зачем!

### Какой диспетчер используется по умолчанию?

**Важно:** Дефолтный диспетчер **НЕ всегда Default**! Зависит от контекста.

#### 1. Наследуется от родительского scope

```kotlin
// viewModelScope использует Dispatchers.Main.immediate
class MyViewModel : ViewModel() {
    fun loadData() {
        viewModelScope.launch {
            // Диспетчер: Main.immediate (унаследован от viewModelScope)
            println(Thread.currentThread().name) // main
        }
    }
}

// lifecycleScope тоже использует Dispatchers.Main.immediate
class MyActivity : AppCompatActivity() {
    fun loadData() {
        lifecycleScope.launch {
            // Диспетчер: Main.immediate (унаследован от lifecycleScope)
            println(Thread.currentThread().name) // main
        }
    }
}

// Свой scope с Dispatchers.IO
class MyRepository : CoroutineScope {
    override val coroutineContext = SupervisorJob() + Dispatchers.IO
    
    fun loadData() {
        launch {
            // Диспетчер: IO (унаследован от coroutineContext)
            println(Thread.currentThread().name) // DefaultDispatcher-worker-1
        }
    }
}
```

#### 2. GlobalScope использует Dispatchers.Default

```kotlin
GlobalScope.launch {
    // Диспетчер: Default (по умолчанию для GlobalScope)
    println(Thread.currentThread().name) // DefaultDispatcher-worker-1
}
```

#### 3. runBlocking использует свой блокирующий диспетчер

```kotlin
fun main() = runBlocking {
    // Диспетчер: BlockingEventLoop (специальный для runBlocking)
    println(Thread.currentThread().name) // main
    
    launch {
        // Наследует от runBlocking
        println(Thread.currentThread().name) // main
    }
}
```

#### 4. coroutineScope и supervisorScope наследуют от родителя

```kotlin
suspend fun loadData() = coroutineScope {
    // Наследует диспетчер от вызывающей корутины
    launch {
        println(Thread.currentThread().name)
    }
}

// Если вызвать из Main:
lifecycleScope.launch { // Main
    loadData() // coroutineScope будет в Main
}

// Если вызвать из IO:
withContext(Dispatchers.IO) { // IO
    loadData() // coroutineScope будет в IO
}
```

#### 5. Явное указание переопределяет наследование

```kotlin
viewModelScope.launch { // Main по умолчанию
    println(Thread.currentThread().name) // main
    
    launch(Dispatchers.IO) { // Явно указали IO
        println(Thread.currentThread().name) // DefaultDispatcher-worker-1
    }
}
```

#### Практические примеры:

```kotlin
class MyViewModel : ViewModel() {
    fun example() {
        // 1. Без указания диспетчера - наследует Main от viewModelScope
        viewModelScope.launch {
            println("1: ${Thread.currentThread().name}") // main
        }
        
        // 2. Явно указали IO - переопределяет Main
        viewModelScope.launch(Dispatchers.IO) {
            println("2: ${Thread.currentThread().name}") // DefaultDispatcher-worker-1
        }
        
        // 3. Вложенная корутина наследует от родителя
        viewModelScope.launch(Dispatchers.IO) {
            println("3a: ${Thread.currentThread().name}") // IO
            
            launch { // Наследует IO от родителя
                println("3b: ${Thread.currentThread().name}") // IO
            }
            
            launch(Dispatchers.Main) { // Явно переопределили
                println("3c: ${Thread.currentThread().name}") // main
            }
        }
    }
}
```

#### Таблица дефолтных диспетчеров:

| Scope / Builder | Дефолтный диспетчер | Примечание |
|-----------------|---------------------|------------|
| `viewModelScope` | **Main.immediate** | Для Android ViewModel |
| `lifecycleScope` | **Main.immediate** | Для Activity/Fragment |
| `GlobalScope` | **Default** | ❌ Не использовать! |
| `runBlocking` | **BlockingEventLoop** | Блокирует поток |
| `coroutineScope` | **Наследует** | От родительской корутины |
| `supervisorScope` | **Наследует** | От родительской корутины |
| `launch { }` | **Наследует** | От scope |
| `async { }` | **Наследует** | От scope |
| `withContext(Dispatchers.X)` | **X** | Явно указан |

#### Важные моменты:

```kotlin
// 1. viewModelScope и lifecycleScope ВСЕГДА Main
viewModelScope.launch {
    // ВСЕГДА в Main потоке
    // Для фоновой работы используй withContext
    withContext(Dispatchers.IO) {
        // Теперь в IO потоке
    }
}

// 2. Вложенные корутины наследуют диспетчер
launch(Dispatchers.IO) {
    launch { // Тоже IO
        launch { // Тоже IO
            // Все в IO
        }
    }
}

// 3. Явное указание всегда переопределяет
launch(Dispatchers.IO) {
    launch(Dispatchers.Main) { // Переопределили на Main
        // Теперь в Main
    }
}
```

#### Распространенная ошибка:

```kotlin
// ❌ ОШИБКА - думаем что это Default, а это Main!
class MyViewModel : ViewModel() {
    fun loadData() {
        viewModelScope.launch { // Это Main, не Default!
            val data = database.query() // Блокирует UI поток!
        }
    }
}

// ✅ ПРАВИЛЬНО
class MyViewModel : ViewModel() {
    fun loadData() {
        viewModelScope.launch {
            val data = withContext(Dispatchers.IO) {
                database.query() // Выполняется в IO потоке
            }
            updateUI(data) // Обратно в Main
        }
    }
}
```

#### Резюме:

**Дефолтный диспетчер:**
- ✅ **Наследуется от scope** (не всегда Default!)
- ✅ **viewModelScope / lifecycleScope** → Main.immediate
- ✅ **GlobalScope** → Default (но не используй!)
- ✅ **Вложенные корутины** → наследуют от родителя
- ✅ **Явное указание** → переопределяет наследование

**Правило:** Всегда явно указывай диспетчер для фоновой работы (`withContext(Dispatchers.IO)`), не полагайся на дефолтный!

### Переключение контекста

```kotlin
suspend fun loadAndShow() {
    val data = withContext(Dispatchers.IO) {
        // Выполняется в IO потоке
        fetchData()
    }
    // Автоматически возвращаемся в исходный диспетчер
    updateUI(data)
}
```

## 3. Coroutine Scope

### CoroutineScope
```kotlin
// Определяет жизненный цикл корутин
class MyClass : CoroutineScope {
    override val coroutineContext: CoroutineContext = 
        Job() + Dispatchers.Main
    
    fun loadData() {
        launch {
            // Корутина привязана к scope
        }
    }
    
    fun cleanup() {
        coroutineContext.cancel() // Отменяет все корутины
    }
}
```

### Android Scopes

#### viewModelScope
```kotlin
class MyViewModel : ViewModel() {
    fun loadData() {
        viewModelScope.launch {
            // Автоматически отменяется при onCleared()
        }
    }
}
```

#### lifecycleScope
```kotlin
class MyActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        lifecycleScope.launch {
            // Привязано к жизненному циклу Activity
        }
        
        // Запуск при определенном состоянии
        lifecycleScope.launchWhenStarted {
            // Выполняется только когда lifecycle >= STARTED
        }
    }
}
```

#### repeatOnLifecycle
```kotlin
// Рекомендуемый способ для сбора Flow
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect { state ->
            updateUI(state)
        }
    }
}
```

### GlobalScope (не рекомендуется)
```kotlin
// Живет весь жизненный цикл приложения
// Использовать только в крайних случаях
GlobalScope.launch {
    // Может привести к утечкам памяти
}
```

## 4. Job и управление корутинами

### Job
```kotlin
val job = launch {
    repeat(1000) { i ->
        println("Job: I'm sleeping $i ...")
        delay(500)
    }
}

delay(1300)
job.cancel() // Отменяет корутину
job.join()   // Ждет завершения
```

### SupervisorJob
```kotlin
// Обычный Job - падение одной корутины отменяет все
val scope = CoroutineScope(Job())
scope.launch { error("Child 1 failed") }
scope.launch { delay(1000) } // Тоже отменится

// SupervisorJob - независимые корутины
val supervisorScope = CoroutineScope(SupervisorJob())
supervisorScope.launch { error("Child 1 failed") }
supervisorScope.launch { delay(1000) } // Продолжит работу
```

### Состояния Job
```kotlin
val job = launch { delay(1000) }

job.isActive    // true во время выполнения
job.isCompleted // true после завершения
job.isCancelled // true после отмены
```

## 5. Обработка ошибок

### try-catch
```kotlin
launch {
    try {
        val data = fetchData()
    } catch (e: Exception) {
        handleError(e)
    }
}
```

### CoroutineExceptionHandler
```kotlin
val handler = CoroutineExceptionHandler { _, exception ->
    println("Caught $exception")
}

val scope = CoroutineScope(Job() + handler)
scope.launch {
    throw Exception("Test")
}
```

### supervisorScope
```kotlin
supervisorScope {
    val child1 = launch {
        throw Exception("Child 1 failed")
    }
    val child2 = launch {
        delay(1000)
        println("Child 2 completed")
    }
}
```

### Отмена и CancellationException
```kotlin
val job = launch {
    try {
        repeat(1000) { i ->
            println("Job: I'm sleeping $i ...")
            delay(500)
        }
    } catch (e: CancellationException) {
        println("Job was cancelled")
        throw e // Важно пробросить дальше
    } finally {
        println("Cleanup")
    }
}

job.cancel()
```

### Проверка отмены
```kotlin
launch {
    while (isActive) { // Проверяет, не отменена ли корутина
        // Работа
    }
}

// Или
launch {
    ensureActive() // Бросает CancellationException если отменена
    // Работа
}
```

## 6. Flow

### Основы Flow
```kotlin
// Холодный поток - не выполняется до collect
fun getNumbers(): Flow<Int> = flow {
    for (i in 1..3) {
        delay(100)
        emit(i) // Испускает значение
    }
}

// Сбор значений
viewModelScope.launch {
    getNumbers().collect { value ->
        println(value)
    }
}
```

### Flow vs Коллекции vs Sequence

#### Сравнительная таблица

| Характеристика | List/Collection | Sequence | Flow |
|----------------|-----------------|----------|------|
| **Выполнение** | Eager (немедленное) | Lazy (ленивое) | Lazy (ленивое) |
| **Асинхронность** | ❌ Синхронные | ❌ Синхронные | ✅ Асинхронные |
| **Suspend функции** | ❌ Нет | ❌ Нет | ✅ Да |
| **Память** | Все в памяти | По элементу | По элементу |
| **Отмена** | ❌ Нет | ❌ Нет | ✅ Да |
| **Множественные значения** | Все сразу | По одному | По одному со временем |
| **Use case** | Готовые данные | CPU-интенсивные операции | Асинхронные потоки |

#### Примеры различий

##### 1. List (Eager - немедленное выполнение)
```kotlin
fun getNumbers(): List<Int> {
    println("Создаем список")
    return listOf(1, 2, 3)
        .map { 
            println("Map: $it")
            it * 2 
        }
        .filter { 
            println("Filter: $it")
            it > 3 
        }
}

val result = getNumbers() // ВСЕ операции выполняются СРАЗУ
println("Получили результат")
// Вывод:
// Создаем список
// Map: 1
// Map: 2
// Map: 3
// Filter: 2
// Filter: 4
// Filter: 6
// Получили результат
```

##### 2. Sequence (Lazy - ленивое выполнение)
```kotlin
fun getNumbers(): Sequence<Int> {
    println("Создаем sequence")
    return sequenceOf(1, 2, 3)
        .map { 
            println("Map: $it")
            it * 2 
        }
        .filter { 
            println("Filter: $it")
            it > 3 
        }
}

val result = getNumbers() // Ничего не выполняется!
println("Получили sequence")
result.forEach { println("Result: $it") } // Выполняется ЗДЕСЬ
// Вывод:
// Создаем sequence
// Получили sequence
// Map: 1
// Filter: 2
// Map: 2
// Filter: 4
// Result: 4
// Map: 3
// Filter: 6
// Result: 6
```

##### 3. Flow (Lazy + Async - ленивое асинхронное)
```kotlin
fun getNumbers(): Flow<Int> {
    println("Создаем flow")
    return flow {
        emit(1)
        emit(2)
        emit(3)
    }
        .map { 
            println("Map: $it")
            delay(100) // Можем использовать suspend функции!
            it * 2 
        }
        .filter { 
            println("Filter: $it")
            it > 3 
        }
}

val result = getNumbers() // Ничего не выполняется!
println("Получили flow")
viewModelScope.launch {
    result.collect { println("Result: $it") } // Выполняется ЗДЕСЬ
}
// Вывод:
// Создаем flow
// Получили flow
// Map: 1
// Filter: 2
// Map: 2
// Filter: 4
// Result: 4
// Map: 3
// Filter: 6
// Result: 6
```

#### Когда использовать что?

##### Используй **List/Collection** когда:
```kotlin
// ✅ Данные уже готовы и небольшие
val users = listOf(user1, user2, user3)

// ✅ Нужен случайный доступ
val user = users[2]

// ✅ Нужно знать размер
val count = users.size

// ✅ Множественные итерации
users.forEach { ... }
users.forEach { ... } // Без повторного вычисления

// ❌ НЕ используй для больших данных
val millionItems = (1..1_000_000).toList() // Все в памяти!
```

##### Используй **Sequence** когда:
```kotlin
// ✅ Большие коллекции с цепочкой операций
(1..1_000_000)
    .asSequence()
    .map { it * 2 }
    .filter { it > 100 }
    .take(10)
    .toList()

// ✅ CPU-интенсивные синхронные операции
files.asSequence()
    .map { parseFile(it) }
    .filter { it.isValid }
    .take(5) // Обработает только 5, остальные не трогает

// ✅ Бесконечные последовательности
generateSequence(0) { it + 1 }
    .take(100)
    .toList()

// ❌ НЕ используй для асинхронных операций
sequence {
    delay(100) // ОШИБКА! suspend функции запрещены
}
```

##### Используй **Flow** когда:
```kotlin
// ✅ Асинхронные операции (сеть, БД)
fun getUsers(): Flow<User> = flow {
    val users = api.fetchUsers() // suspend функция
    users.forEach { emit(it) }
}

// ✅ Потоки данных со временем
fun observeLocation(): Flow<Location> = callbackFlow {
    locationManager.requestUpdates { location ->
        trySend(location)
    }
}

// ✅ Реактивные обновления
fun observeDatabase(): Flow<List<User>> = 
    database.getUsersFlow() // Room возвращает Flow

// ✅ Нужна отмена
viewModelScope.launch {
    repository.getData()
        .collect { data ->
            updateUI(data)
        }
} // Автоматически отменится

// ✅ Обработка ошибок и retry
flow { api.getData() }
    .retry(3)
    .catch { emit(defaultValue) }
    .collect()
```

#### Производительность и память

```kotlin
// List - ВСЕ в памяти сразу
val list = (1..1_000_000)
    .map { it * 2 }        // Создает список из 1М элементов
    .filter { it > 100 }   // Создает еще один список
    .take(10)              // Создает список из 10 элементов
// Итого: ~3 списка в памяти!

// Sequence - по одному элементу
val sequence = (1..1_000_000)
    .asSequence()
    .map { it * 2 }        // Ничего не создается
    .filter { it > 100 }   // Ничего не создается
    .take(10)              // Обработает только 60 элементов (1..60)
    .toList()
// Итого: обработано 60 элементов, в памяти только результат [102, 104, ..., 120]

// Flow - по одному элементу + асинхронность
val flow = (1..1_000_000)
    .asFlow()
    .map { 
        delay(1) // Можем делать async операции
        it * 2 
    }
    .filter { it > 100 }
    .take(10)
    .toList()
```

#### Конвертация между типами

```kotlin
// List → Sequence
val sequence = list.asSequence()

// List → Flow
val flow = list.asFlow()

// Sequence → List
val list = sequence.toList()

// Flow → List (suspend)
val list = flow.toList()

// Flow → Sequence (НЕ рекомендуется - теряется асинхронность)
// Нет прямой конвертации
```

#### Практические примеры

##### Пример 1: Обработка файлов
```kotlin
// ❌ List - все файлы в памяти
fun processFiles(files: List<File>): List<Data> {
    return files
        .map { parseFile(it) }      // Парсит ВСЕ файлы
        .filter { it.isValid }
        .take(10)
}

// ✅ Sequence - ленивая обработка
fun processFiles(files: List<File>): List<Data> {
    return files
        .asSequence()
        .map { parseFile(it) }      // Парсит только нужные
        .filter { it.isValid }
        .take(10)
        .toList()
}

// ✅ Flow - асинхронная обработка
fun processFiles(files: List<File>): Flow<Data> = flow {
    files.forEach { file ->
        val data = withContext(Dispatchers.IO) {
            parseFile(file)
        }
        if (data.isValid) {
            emit(data)
        }
    }
}.take(10)
```

##### Пример 2: Загрузка данных
```kotlin
// ❌ List - блокирует поток
fun loadUsers(): List<User> {
    return api.getUsers() // Блокирующий вызов
}

// ❌ Sequence - все еще блокирует
fun loadUsers(): Sequence<User> {
    return api.getUsers().asSequence()
}

// ✅ Flow - асинхронно
fun loadUsers(): Flow<User> = flow {
    val users = api.getUsers() // suspend функция
    users.forEach { emit(it) }
}
```

##### Пример 3: Наблюдение за БД
```kotlin
// ❌ List - одноразовое чтение
fun getUsers(): List<User> {
    return database.getUsers() // Только текущее состояние
}

// ✅ Flow - реактивные обновления
fun observeUsers(): Flow<List<User>> {
    return database.getUsersFlow() // Обновляется автоматически
}

// Использование
viewModelScope.launch {
    repository.observeUsers().collect { users ->
        _uiState.value = UiState.Success(users)
        // Будет вызываться при каждом изменении БД!
    }
}
```

#### Резюме: Когда что использовать

**List:**
- Маленькие коллекции
- Данные уже в памяти
- Нужен случайный доступ или размер
- Множественные итерации

**Sequence:**
- Большие коллекции
- Цепочки трансформаций
- CPU-интенсивные синхронные операции
- Хотим избежать промежуточных коллекций

**Flow:**
- Асинхронные операции (сеть, БД, файлы)
- Потоки данных со временем
- Реактивные обновления
- Нужна отмена и обработка ошибок
- Android UI (StateFlow, SharedFlow)

### Flow операторы

#### Промежуточные операторы (intermediate)
```kotlin
flow {
    emit(1)
    emit(2)
    emit(3)
}
    .map { it * 2 }           // 2, 4, 6
    .filter { it > 3 }        // 4, 6
    .take(1)                  // 4
    .onEach { println(it) }   // Side-effect
    .collect()

// Другие операторы
flowOf(1, 2, 3)
    .transform { value ->
        emit(value)
        emit(value * 2)
    }
    .distinctUntilChanged()
    .debounce(300)
    .flatMapConcat { flow { emit(it) } }
    .catch { e -> emit(-1) } // Обработка ошибок
    .collect()
```

#### Терминальные операторы (terminal)
```kotlin
val flow = flowOf(1, 2, 3)

flow.collect { value -> println(value) }
val list = flow.toList()
val first = flow.first()
val single = flow.single()
val count = flow.count()
val reduced = flow.reduce { acc, value -> acc + value }
```

### flowOn - переключение контекста
```kotlin
fun loadData(): Flow<String> = flow {
    // Выполняется в IO
    val data = fetchFromNetwork()
    emit(data)
}.flowOn(Dispatchers.IO)

// Сбор в Main
viewModelScope.launch {
    loadData().collect { data ->
        // Выполняется в Main
        updateUI(data)
    }
}
```

### Обработка ошибок в Flow
```kotlin
flow {
    emit(1)
    throw Exception("Error")
}
    .catch { e -> 
        println("Caught: $e")
        emit(-1) // Можно испустить fallback значение
    }
    .collect { println(it) }

// retry
flow { 
    if (Random.nextBoolean()) throw Exception()
    emit("Success")
}
    .retry(3) { cause ->
        cause is IOException
    }
    .collect()
```

### Buffer и conflate
```kotlin
// buffer - буферизация значений
flow {
    repeat(3) {
        delay(100)
        emit(it)
    }
}
    .buffer() // Производитель не ждет потребителя
    .collect {
        delay(300)
        println(it)
    }

// conflate - пропускает промежуточные значения
flow {
    repeat(10) {
        delay(100)
        emit(it)
    }
}
    .conflate() // Берет только последнее значение
    .collect {
        delay(300)
        println(it)
    }
```

## 7. StateFlow

### Основы StateFlow
```kotlin
class MyViewModel : ViewModel() {
    // Горячий поток с начальным значением
    private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()
    
    fun loadData() {
        viewModelScope.launch {
            _uiState.value = UiState.Loading
            try {
                val data = repository.getData()
                _uiState.value = UiState.Success(data)
            } catch (e: Exception) {
                _uiState.value = UiState.Error(e.message)
            }
        }
    }
}

sealed class UiState {
    object Loading : UiState()
    data class Success(val data: String) : UiState()
    data class Error(val message: String?) : UiState()
}
```

### Сбор StateFlow
```kotlin
// В Activity/Fragment
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect { state ->
            when (state) {
                is UiState.Loading -> showLoading()
                is UiState.Success -> showData(state.data)
                is UiState.Error -> showError(state.message)
            }
        }
    }
}

// В Compose
@Composable
fun MyScreen(viewModel: MyViewModel) {
    val uiState by viewModel.uiState.collectAsState()
    
    when (uiState) {
        is UiState.Loading -> LoadingView()
        is UiState.Success -> SuccessView(uiState.data)
        is UiState.Error -> ErrorView(uiState.message)
    }
}
```

### Особенности StateFlow
```kotlin
// 1. Всегда имеет значение
val state = _uiState.value // Можно получить текущее значение

// 2. Conflated - хранит только последнее значение
_uiState.value = 1
_uiState.value = 2
_uiState.value = 3
// Подписчик получит только 3

// 3. Не испускает одинаковые значения подряд
_uiState.value = "A"
_uiState.value = "A" // Не испустится
_uiState.value = "B" // Испустится

// 4. update - атомарное обновление
_uiState.update { currentState ->
    currentState.copy(count = currentState.count + 1)
}
```

### Комбинирование StateFlow
```kotlin
class MyViewModel : ViewModel() {
    private val _name = MutableStateFlow("")
    private val _age = MutableStateFlow(0)
    
    val userInfo: StateFlow<String> = combine(_name, _age) { name, age ->
        "Name: $name, Age: $age"
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = ""
    )
}
```

## 8. SharedFlow

### Основы SharedFlow
```kotlin
class MyViewModel : ViewModel() {
    // Горячий поток для событий
    private val _events = MutableSharedFlow<Event>()
    val events: SharedFlow<Event> = _events.asSharedFlow()
    
    fun onButtonClick() {
        viewModelScope.launch {
            _events.emit(Event.ShowToast("Clicked!"))
        }
    }
}

sealed class Event {
    data class ShowToast(val message: String) : Event()
    object NavigateBack : Event()
}
```

### Параметры SharedFlow
```kotlin
// replay - количество кешируемых значений для новых подписчиков
// extraBufferCapacity - дополнительный буфер
// onBufferOverflow - стратегия при переполнении буфера
private val _events = MutableSharedFlow<Event>(
    replay = 0,              // Не кешировать
    extraBufferCapacity = 1, // Буфер на 1 элемент
    onBufferOverflow = BufferOverflow.DROP_OLDEST
)

// Стратегии переполнения:
// SUSPEND - приостановить emit (по умолчанию)
// DROP_OLDEST - удалить самое старое значение
// DROP_LATEST - удалить новое значение
```

### Сбор SharedFlow
```kotlin
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.events.collect { event ->
            when (event) {
                is Event.ShowToast -> showToast(event.message)
                is Event.NavigateBack -> navigateBack()
            }
        }
    }
}
```

### SharedFlow vs StateFlow
```kotlin
// StateFlow - для состояния
// - Всегда имеет значение
// - Conflated (только последнее)
// - Пропускает одинаковые значения ПОДРЯД
private val _uiState = MutableStateFlow("Initial")

// Пример:
_uiState.value = "A"  // Испустится (новое значение)
_uiState.value = "A"  // НЕ испустится (одинаковое подряд)
_uiState.value = "B"  // Испустится (изменилось)
_uiState.value = "A"  // Испустится (изменилось, хоть и было раньше)

// SharedFlow - для событий (one-time events)
// - Может не иметь значения
// - Может доставить все события
// - НЕ пропускает дубликаты (даже подряд)
private val _events = MutableSharedFlow<Event>()

// Пример:
_events.emit(Event.Click) // Испустится
_events.emit(Event.Click) // Испустится (дубликат тоже)
_events.emit(Event.Click) // Испустится (все события доставляются)
```

## 9. LiveData vs Flow/StateFlow

### LiveData
```kotlin
class MyViewModel : ViewModel() {
    private val _data = MutableLiveData<String>()
    val data: LiveData<String> = _data
    
    fun loadData() {
        viewModelScope.launch {
            _data.value = fetchData()
        }
    }
}

// Наблюдение
viewModel.data.observe(viewLifecycleOwner) { data ->
    updateUI(data)
}
```

### Сравнение

| Характеристика | LiveData | StateFlow | SharedFlow |
|----------------|----------|-----------|------------|
| Lifecycle aware | ✅ Да | ❌ Нет (нужен repeatOnLifecycle) | ❌ Нет |
| Начальное значение | ❌ Опционально | ✅ Обязательно | ❌ Нет |
| Поддержка операторов | ⚠️ Ограничена | ✅ Все Flow операторы | ✅ Все Flow операторы |
| Потокобезопасность | ✅ Да | ✅ Да | ✅ Да |
| Replay | ❌ Нет | ✅ Последнее значение | ⚙️ Настраивается |
| Multiplatform | ❌ Только Android | ✅ KMP | ✅ KMP |

### Конвертация LiveData <-> Flow
```kotlin
// LiveData -> Flow
val flow = liveData.asFlow()

// Flow -> LiveData
val liveData = flow.asLiveData()

// StateFlow -> LiveData
val liveData = stateFlow.asLiveData()
```

### Когда использовать что?

#### LiveData - используй когда:

```kotlin
// ✅ Простое наблюдение - меньше boilerplate
viewModel.user.observe(viewLifecycleOwner) { user ->
    updateUI(user) // Автоматически управляет lifecycle
}

// ✅ Data Binding в XML
class UserViewModel : ViewModel() {
    val userName = MutableLiveData<String>()
    // Используется в layout: android:text="@{viewModel.userName}"
}

// ✅ Legacy проекты на LiveData
```

**Преимущества LiveData:**
- Автоматическая lifecycle awareness (не нужен repeatOnLifecycle)
- Меньше кода для простых случаев
- Интеграция с Data Binding

**Недостатки LiveData:**
- Ограниченный набор операторов (нет debounce, filter, combine)
- Только Android (не KMP)
- Не работает с Compose

#### StateFlow - используй когда:

```kotlin
// ✅ Сложные трансформации
val results = searchQuery
    .debounce(300)
    .filter { it.length >= 3 }
    .flatMapLatest { repository.search(it) }
    .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

// ✅ KMP проекты
class SharedViewModel { // Работает на Android и iOS
    val state: StateFlow<UiState> = ...
}

// ✅ Compose UI
@Composable
fun Screen(viewModel: VM) {
    val state by viewModel.state.collectAsState()
}

// ✅ Реактивные обновления из Room
@Dao
interface UserDao {
    @Query("SELECT * FROM users")
    fun observeUsers(): Flow<List<User>> // Автоматически обновляется
}
```

**Преимущества StateFlow:**
- Богатый набор операторов (debounce, filter, combine, retry, catch)
- Kotlin Multiplatform
- Идеально для Compose
- Реактивные обновления из БД

**Недостатки StateFlow:**
- Больше boilerplate (нужен repeatOnLifecycle)
- Обязательное начальное значение

#### SharedFlow - используй когда:

```kotlin
// ✅ One-time события
private val _events = MutableSharedFlow<Event>()
val events = _events.asSharedFlow()

fun onButtonClick() {
    viewModelScope.launch {
        _events.emit(Event.ShowToast("Clicked"))
    }
}
```

#### Практическое сравнение:

```kotlin
// LiveData - 3 строки
viewModel.user.observe(viewLifecycleOwner) { updateUI(it) }

// StateFlow - 7 строк
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.user.collect { updateUI(it) }
    }
}

// НО StateFlow дает больше возможностей:
val filtered = flow.filter { it.isValid }.debounce(300).distinctUntilChanged()
// LiveData такого не умеет!
```

#### Резюме:

**LiveData:** простые случаи в XML UI, Data Binding, legacy код  
**StateFlow:** сложная логика, KMP, Compose, новые проекты (рекомендуется)  
**SharedFlow:** события (navigation, toast, snackbar)

**Тренд:** Google рекомендует Flow для новых проектов

## 10. stateIn и shareIn

### stateIn - конвертация Flow в StateFlow
```kotlin
class MyViewModel : ViewModel() {
    val uiState: StateFlow<UiState> = repository.getData()
        .map { data -> UiState.Success(data) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = UiState.Loading
        )
}
```

### shareIn - конвертация Flow в SharedFlow
```kotlin
val sharedFlow: SharedFlow<Data> = repository.getData()
    .shareIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        replay = 1
    )
```

### SharingStarted стратегии
```kotlin
// Eagerly - начинает сразу, останавливается при отмене scope
SharingStarted.Eagerly

// Lazily - начинает при первом подписчике, никогда не останавливается
SharingStarted.Lazily

// WhileSubscribed - начинает при первом подписчике, 
// останавливается через stopTimeoutMillis после последнего
SharingStarted.WhileSubscribed(
    stopTimeoutMillis = 5000,
    replayExpirationMillis = 0
)
```

## 11. Каналы (Channels)

### Основы Channel
```kotlin
// Горячий поток для коммуникации между корутинами
val channel = Channel<Int>()

// Отправка
launch {
    for (x in 1..5) {
        channel.send(x)
    }
    channel.close()
}

// Получение
launch {
    for (y in channel) {
        println(y)
    }
}
```

### Типы каналов
```kotlin
// Rendezvous (по умолчанию) - capacity = 0
val channel1 = Channel<Int>()

// Buffered - с буфером
val channel2 = Channel<Int>(10)

// Unlimited - неограниченный буфер
val channel3 = Channel<Int>(Channel.UNLIMITED)

// Conflated - хранит только последнее значение
val channel4 = Channel<Int>(Channel.CONFLATED)
```

### Channel vs Flow
```kotlin
// Channel - горячий, для коммуникации
val channel = Channel<Int>()
launch { channel.send(1) } // Отправляется даже без получателя

// Flow - холодный, для потоков данных
val flow = flow { emit(1) } // Не выполняется до collect
```

## 12. Продвинутые темы

### Structured Concurrency (Структурированная конкурентность)

#### Что это такое?

**Structured Concurrency** - это принцип, при котором корутины организованы в **иерархию** (дерево), где:
1. **Родитель ждет завершения всех детей**
2. **Отмена родителя отменяет всех детей**
3. **Ошибка в ребенке отменяет родителя и всех siblings**
4. **Корутины привязаны к scope с определенным жизненным циклом**

#### Основные правила:

```kotlin
// 1. Родитель ждет всех детей
suspend fun loadData() = coroutineScope {
    launch { 
        delay(1000)
        println("Child 1")
    }
    launch { 
        delay(2000)
        println("Child 2")
    }
    println("Parent starts")
}
// Вывод:
// Parent starts
// Child 1 (через 1 сек)
// Child 2 (через 2 сек)
// loadData() завершится только после Child 2!

// 2. Отмена родителя отменяет детей
val job = launch {
    launch { 
        repeat(100) {
            delay(100)
            println("Child working...")
        }
    }
}
delay(500)
job.cancel() // Отменит и родителя, и ребенка

// 3. Ошибка в ребенке отменяет всех (с обычным Job)
coroutineScope {
    launch {
        delay(1000)
        println("Child 1 done")
    }
    launch {
        delay(500)
        throw Exception("Child 2 failed") // Отменит Child 1 тоже!
    }
}
```

#### Иерархия корутин:

```
CoroutineScope (viewModelScope)
    │
    ├─ Job (родительская корутина)
    │   │
    │   ├─ Job (дочерняя корутина 1)
    │   │   └─ Job (внучатая корутина)
    │   │
    │   └─ Job (дочерняя корутина 2)
    │
    └─ Job (другая родительская корутина)
```

#### Пример правильной Structured Concurrency:

```kotlin
class MyViewModel : ViewModel() {
    fun loadData() {
        viewModelScope.launch { // Родитель
            val user = async { fetchUser() }     // Ребенок 1
            val posts = async { fetchPosts() }   // Ребенок 2
            
            // viewModelScope ждет завершения всех детей
            val userData = user.await()
            val postsData = posts.await()
            
            _uiState.value = UiState.Success(userData, postsData)
        }
    }
    
    override fun onCleared() {
        // viewModelScope.cancel() отменит ВСЕ дочерние корутины
        super.onCleared()
    }
}
```

#### Почему GlobalScope НАРУШАЕТ Structured Concurrency?

**GlobalScope** - это scope без родителя, который живет весь жизненный цикл приложения.

##### Проблема 1: Нет привязки к жизненному циклу

```kotlin
// ❌ ПЛОХО - нарушает Structured Concurrency
class MyActivity : AppCompatActivity() {
    fun loadData() {
        GlobalScope.launch {
            val data = fetchData() // Долгая операция
            updateUI(data) // CRASH! Activity может быть уничтожена
        }
    }
}
// Проблема: корутина продолжит работу даже после destroy Activity
// Результат: утечка памяти + возможный краш

// ✅ ХОРОШО - соблюдает Structured Concurrency
class MyActivity : AppCompatActivity() {
    fun loadData() {
        lifecycleScope.launch { // Привязано к lifecycle
            val data = fetchData()
            updateUI(data) // Безопасно
        }
    }
}
// lifecycleScope автоматически отменится при onDestroy()
```

##### Проблема 2: Невозможно отменить

```kotlin
// ❌ ПЛОХО
class MyViewModel : ViewModel() {
    fun loadData() {
        GlobalScope.launch {
            repeat(1000) {
                delay(1000)
                println("Working...")
            }
        }
    }
    
    override fun onCleared() {
        // Корутина НЕ отменится! Будет работать вечно!
        super.onCleared()
    }
}

// ✅ ХОРОШО
class MyViewModel : ViewModel() {
    fun loadData() {
        viewModelScope.launch {
            repeat(1000) {
                delay(1000)
                println("Working...")
            }
        }
    }
    
    override fun onCleared() {
        // viewModelScope автоматически отменит все корутины
        super.onCleared()
    }
}
```

##### Проблема 3: Нет иерархии

```kotlin
// ❌ ПЛОХО - корутины не связаны
GlobalScope.launch {
    launch { task1() } // Независимая
    launch { task2() } // Независимая
    launch { task3() } // Независимая
}
// Если одна упадет, остальные продолжат работу
// Нет контроля над всеми задачами

// ✅ ХОРОШО - есть иерархия
viewModelScope.launch {
    launch { task1() } // Дочерняя
    launch { task2() } // Дочерняя
    launch { task3() } // Дочерняя
}
// Если родитель отменится, отменятся все дети
// Если одна упадет (без SupervisorJob), отменятся все
```

##### Проблема 4: Утечки памяти

```kotlin
// ❌ ПЛОХО
class UserRepository(private val api: ApiService) {
    fun observeUser(id: String) {
        GlobalScope.launch {
            while (true) {
                val user = api.getUser(id)
                // Обновляем что-то
                delay(5000)
            }
        }
    }
}
// Корутина НИКОГДА не остановится!
// Repository может быть пересоздан, но старые корутины продолжат работу
// Результат: множество корутин работают параллельно = утечка памяти

// ✅ ХОРОШО
class UserRepository(private val api: ApiService) : CoroutineScope {
    override val coroutineContext = SupervisorJob() + Dispatchers.IO
    
    fun observeUser(id: String) {
        launch { // Используем свой scope
            while (isActive) {
                val user = api.getUser(id)
                delay(5000)
            }
        }
    }
    
    fun cleanup() {
        coroutineContext.cancel() // Отменяем все корутины
    }
}
```

#### Когда GlobalScope допустим?

**Очень редко!** Только для:

```kotlin
// 1. Логирование (не критично если потеряется)
fun logEvent(event: String) {
    GlobalScope.launch {
        analyticsService.log(event)
    }
}

// 2. Фоновая работа всего приложения
class App : Application() {
    override fun onCreate() {
        super.onCreate()
        GlobalScope.launch {
            // Периодическая очистка кеша всего приложения
            while (true) {
                delay(24.hours)
                cleanupCache()
            }
        }
    }
}

// Но даже здесь лучше использовать свой scope!
```

#### Правильные альтернативы GlobalScope:

```kotlin
// 1. viewModelScope - для ViewModel
class MyViewModel : ViewModel() {
    fun loadData() {
        viewModelScope.launch { }
    }
}

// 2. lifecycleScope - для Activity/Fragment
class MyActivity : AppCompatActivity() {
    fun loadData() {
        lifecycleScope.launch { }
    }
}

// 3. Свой scope - для других классов
class MyRepository : CoroutineScope {
    private val job = SupervisorJob()
    override val coroutineContext = job + Dispatchers.IO
    
    fun loadData() {
        launch { }
    }
    
    fun cleanup() {
        job.cancel()
    }
}

// 4. coroutineScope / supervisorScope - для suspend функций
suspend fun loadData() = coroutineScope {
    val user = async { fetchUser() }
    val posts = async { fetchPosts() }
    UserData(user.await(), posts.await())
}
```

#### Резюме: Structured Concurrency

**Что это:**
- Корутины организованы в иерархию
- Родитель контролирует детей
- Автоматическая отмена и управление жизненным циклом

**Преимущества:**
- ✅ Нет утечек памяти
- ✅ Автоматическая очистка ресурсов
- ✅ Предсказуемое поведение
- ✅ Легко отменить все связанные задачи

**GlobalScope нарушает это потому что:**
- ❌ Нет родителя (живет вечно)
- ❌ Нет привязки к жизненному циклу
- ❌ Невозможно автоматически отменить
- ❌ Приводит к утечкам памяти

**Правило:** Почти НИКОГДА не используй GlobalScope в Android!

#### Пример нарушения vs соблюдения:

```kotlin
// ❌ Нарушение Structured Concurrency
fun loadUserData() {
    GlobalScope.launch {
        val user = fetchUser()
        GlobalScope.launch {
            val posts = fetchPosts(user.id)
            GlobalScope.launch {
                val comments = fetchComments(posts)
                // Корутины не связаны, невозможно отменить все
            }
        }
    }
}

// ✅ Соблюдение Structured Concurrency
suspend fun loadUserData() = coroutineScope {
    val user = fetchUser()
    val posts = async { fetchPosts(user.id) }
    val comments = async { fetchComments(posts.await()) }
    
    UserData(user, posts.await(), comments.await())
    // Все корутины связаны, отмена одной отменит все
}
```

### CoroutineContext
```kotlin
// Набор элементов: Job, Dispatcher, Name, ExceptionHandler
val context: CoroutineContext = 
    Job() + 
    Dispatchers.Main + 
    CoroutineName("MyCoroutine") +
    CoroutineExceptionHandler { _, e -> }

launch(context) {
    println(coroutineContext[CoroutineName]?.name)
}
```

### withTimeout и withTimeoutOrNull
```kotlin
try {
    withTimeout(1000) {
        delay(2000)
    }
} catch (e: TimeoutCancellationException) {
    println("Timeout!")
}

// Возвращает null вместо исключения
val result = withTimeoutOrNull(1000) {
    delay(2000)
    "Success"
} // result = null
```

### Mutex для синхронизации
```kotlin
val mutex = Mutex()
var counter = 0

repeat(1000) {
    launch {
        mutex.withLock {
            counter++
        }
    }
}
```

### Select expression
```kotlin
suspend fun selectExample() {
    val channel1 = Channel<String>()
    val channel2 = Channel<String>()
    
    launch { channel1.send("from channel 1") }
    launch { channel2.send("from channel 2") }
    
    select<Unit> {
        channel1.onReceive { value ->
            println(value)
        }
        channel2.onReceive { value ->
            println(value)
        }
    }
}
```

## 13. Тестирование корутин

### TestDispatcher
```kotlin
@Test
fun testCoroutine() = runTest {
    val viewModel = MyViewModel()
    viewModel.loadData()
    
    // Время виртуальное, delay выполняется мгновенно
    advanceUntilIdle()
    
    assertEquals(expected, viewModel.uiState.value)
}
```

### Тестирование Flow
```kotlin
@Test
fun testFlow() = runTest {
    val flow = flowOf(1, 2, 3)
    
    val result = flow.toList()
    assertEquals(listOf(1, 2, 3), result)
}

// Turbine библиотека для тестирования Flow
@Test
fun testStateFlow() = runTest {
    viewModel.uiState.test {
        assertEquals(UiState.Loading, awaitItem())
        viewModel.loadData()
        assertEquals(UiState.Success, awaitItem())
    }
}
```

### Внедрение TestDispatcher
```kotlin
class MyViewModel(
    private val dispatcher: CoroutineDispatcher = Dispatchers.IO
) : ViewModel() {
    fun loadData() {
        viewModelScope.launch(dispatcher) {
            // ...
        }
    }
}

// В тесте
@Test
fun test() = runTest {
    val viewModel = MyViewModel(StandardTestDispatcher(testScheduler))
    // ...
}
```

## 14. Best Practices

### 1. Используйте правильные scope
```kotlin
// ✅ Правильно
class MyViewModel : ViewModel() {
    fun loadData() {
        viewModelScope.launch {
            // Автоматически отменится
        }
    }
}

// ❌ Неправильно
class MyViewModel : ViewModel() {
    fun loadData() {
        GlobalScope.launch {
            // Утечка памяти
        }
    }
}
```

### 2. Обрабатывайте отмену
```kotlin
// ✅ Правильно
launch {
    try {
        while (isActive) {
            // Работа
        }
    } finally {
        // Cleanup
    }
}

// ❌ Неправильно
launch {
    while (true) {
        // Не проверяет отмену
    }
}
```

### 3. Используйте withContext вместо launch для возврата результата
```kotlin
// ✅ Правильно
suspend fun loadData(): String = withContext(Dispatchers.IO) {
    fetchData()
}

// ❌ Неправильно
fun loadData(): String {
    var result = ""
    viewModelScope.launch(Dispatchers.IO) {
        result = fetchData() // Race condition
    }
    return result
}
```

### 4. StateFlow для состояния, SharedFlow для событий
```kotlin
// ✅ Правильно
private val _uiState = MutableStateFlow(UiState.Initial)
private val _events = MutableSharedFlow<Event>()

// ❌ Неправильно - события в StateFlow могут потеряться
private val _events = MutableStateFlow<Event?>(null)
```

### 5. Используйте repeatOnLifecycle для сбора Flow
```kotlin
// ✅ Правильно
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect { }
    }
}

// ❌ Неправильно - продолжает работать в background
lifecycleScope.launch {
    viewModel.uiState.collect { }
}
```

### 6. Обрабатывайте ошибки
```kotlin
// ✅ Правильно
viewModelScope.launch {
    try {
        val data = repository.getData()
        _uiState.value = UiState.Success(data)
    } catch (e: Exception) {
        _uiState.value = UiState.Error(e.message)
    }
}

// Или с CoroutineExceptionHandler
val handler = CoroutineExceptionHandler { _, e ->
    _uiState.value = UiState.Error(e.message)
}
viewModelScope.launch(handler) {
    val data = repository.getData()
    _uiState.value = UiState.Success(data)
}
```

### 7. Используйте правильные диспетчеры
```kotlin
// ✅ Правильно
suspend fun loadFromDb() = withContext(Dispatchers.IO) {
    database.query()
}

suspend fun calculate() = withContext(Dispatchers.Default) {
    heavyComputation()
}

// ❌ Неправильно - блокирует Main поток
suspend fun loadFromDb() {
    database.query() // Выполняется в Main
}
```

## 15. Частые вопросы на собеседовании

### Q: В чем разница между launch и async?
**A:** `launch` возвращает `Job` и используется для fire-and-forget операций. `async` возвращает `Deferred<T>` и используется когда нужен результат через `await()`.

### Q: Что такое structured concurrency?
**A:** Принцип, при котором дочерние корутины привязаны к родительской. Родитель ждет завершения всех детей, а отмена родителя отменяет всех детей.

### Q: В чем разница между Job и SupervisorJob?
**A:** При `Job` падение одной дочерней корутины отменяет все остальные. При `SupervisorJob` корутины независимы.

### Q: Что происходит при отмене корутины?
**A:** Бросается `CancellationException`, выполняется блок `finally`, корутина переходит в состояние cancelled. Важно проверять `isActive` в циклах.

### Q: В чем разница между cold и hot Flow?
**A:** Cold Flow (обычный Flow) начинает работу только при `collect`, каждый подписчик получает свой поток. Hot Flow (StateFlow, SharedFlow) работает независимо от подписчиков.

### Q: Когда использовать StateFlow, а когда SharedFlow?
**A:** `StateFlow` для состояния UI (всегда имеет значение, conflated). `SharedFlow` для событий (может не иметь значения, настраиваемый replay).

### Q: Зачем нужен repeatOnLifecycle?
**A:** Чтобы автоматически останавливать сбор Flow когда UI не видим (например в background), избегая лишней работы и крашей при обновлении UI.

### Q: В чем разница между Dispatchers.IO и Dispatchers.Default?
**A:** `IO` для I/O операций (сеть, БД, файлы), пул до 64 потоков. `Default` для CPU-интенсивных задач, пул = количество ядер.

### Q: Что такое Continuation?
**A:** Объект, представляющий продолжение выполнения suspend функции. Компилятор преобразует suspend функции в state machine с Continuation.

### Q: Как работает delay() под капотом?
**A:** Приостанавливает корутину, освобождая поток. Использует `Delay` интерфейс диспетчера для планирования возобновления через заданное время.

## 16. Типичные ошибки

### 1. Утечки памяти
```kotlin
// ❌ Неправильно
class MyActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {wwwwwwe
        GlobalScope.launch {
            // Activity может быть уничтожена, но корутина продолжит работу
        }
    }
}

// ✅ Правильно
class MyActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        lifecycleScope.launch {
            // Автоматически отменится
        }
    }
}
```

### 2. Блокировка Main потока
```kotlin
// ❌ Неправильно
fun loadData() {
    runBlocking {
        delay(1000) // Блокирует UI
    }
}

// ✅ Правильно
fun loadData() {
    viewModelScope.launch {
        delay(1000) // Не блокирует UI
    }
}
```

### 3. Игнорирование CancellationException
```kotlin
// ❌ Неправильно
launch {
    try {
        delay(1000)
    } catch (e: Exception) {
        // Поглощает CancellationException
    }
}

// ✅ Правильно
launch {
    try {
        delay(1000)
    } catch (e: CancellationException) {
        throw e // Пробрасываем дальше
    } catch (e: Exception) {
        // Обрабатываем другие ошибки
    }
}
```

### 4. Неправильное использование Flow в UI
```kotlin
// ❌ Неправильно - продолжает работать в background
lifecycleScope.launch {
    viewModel.uiState.collect { state ->
        updateUI(state) // Может крашнуться если UI уничтожен
    }
}

// ✅ Правильно
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect { state ->
            updateUI(state)
        }
    }
}
```

### 5. Использование .value вместо .emit() для SharedFlow
```kotlin
// ❌ Неправильно - у SharedFlow нет .value
private val _events = MutableSharedFlow<Event>()
_events.value = Event.Click // Ошибка компиляции

// ✅ Правильно
viewModelScope.launch {
    _events.emit(Event.Click)
}
```

## 17. Паттерны использования

### Repository паттерн
```kotlin
class UserRepository(
    private val api: ApiService,
    private val db: UserDao
) {
    fun getUser(id: String): Flow<User> = flow {
        // Сначала из кеша
        val cached = db.getUser(id)
        if (cached != null) {
            emit(cached)
        }
        
        // Затем из сети
        val fresh = api.getUser(id)
        db.insertUser(fresh)
        emit(fresh)
    }.flowOn(Dispatchers.IO)
}
```

### ViewModel с состоянием
```kotlin
class UserViewModel(
    private val repository: UserRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()
    
    private val _events = MutableSharedFlow<Event>()
    val events: SharedFlow<Event> = _events.asSharedFlow()
    
    fun loadUser(id: String) {
        viewModelScope.launch {
            _uiState.value = UiState.Loading
            
            repository.getUser(id)
                .catch { e ->
                    _uiState.value = UiState.Error(e.message)
                    _events.emit(Event.ShowError(e.message))
                }
                .collect { user ->
                    _uiState.value = UiState.Success(user)
                }
        }
    }
    
    fun retry() {
        loadUser(currentUserId)
    }
}
```

### Use Case с корутинами
```kotlin
class GetUserUseCase(
    private val repository: UserRepository,
    private val dispatcher: CoroutineDispatcher = Dispatchers.IO
) {
    suspend operator fun invoke(id: String): Result<User> = 
        withContext(dispatcher) {
            try {
                Result.success(repository.getUser(id))
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
}
```

## 18. Производительность

### Избегайте создания лишних корутин
```kotlin
// ❌ Неправильно
fun loadUsers(ids: List<String>) {
    ids.forEach { id ->
        viewModelScope.launch {
            loadUser(id)
        }
    }
}

// ✅ Правильно
fun loadUsers(ids: List<String>) {
    viewModelScope.launch {
        ids.forEach { id ->
            loadUser(id)
        }
    }
}
```

### Используйте buffer для производительности
```kotlin
flow {
    repeat(100) {
        emit(it)
        delay(100) // Медленный производитель
    }
}
    .buffer() // Не ждет обработки предыдущего
    .collect {
        delay(300) // Медленный потребитель
        println(it)
    }
```

### Параллельное выполнение с async
```kotlin
suspend fun loadData() = coroutineScope {
    val user = async { fetchUser() }
    val posts = async { fetchPosts() }
    val comments = async { fetchComments() }
    
    // Все выполняются параллельно
    Triple(user.await(), posts.await(), comments.await())
}
```

## 19. Тестирование корутин

### Зависимости
```kotlin
// build.gradle.kts
testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
testImplementation("io.mockk:mockk:1.13.8")
```

### 1. Простой Unit тест с runTest

```kotlin
class UserRepository(private val api: ApiService) {
    suspend fun getUser(id: String): User {
        return api.fetchUser(id)
    }
}

// Тест
class UserRepositoryTest {
    @Test
    fun `getUser returns user from api`() = runTest {
        // Given
        val api = mockk<ApiService>()
        val expectedUser = User("1", "John")
        coEvery { api.fetchUser("1") } returns expectedUser
        
        val repository = UserRepository(api)
        
        // When
        val result = repository.getUser("1")
        
        // Then
        assertEquals(expectedUser, result)
        coVerify { api.fetchUser("1") }
    }
}
```

### 2. Тестирование ViewModel с StateFlow

```kotlin
class UserViewModel(private val repository: UserRepository) : ViewModel() {
    private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()
    
    fun loadUser(id: String) {
        viewModelScope.launch {
            _uiState.value = UiState.Loading
            try {
                val user = repository.getUser(id)
                _uiState.value = UiState.Success(user)
            } catch (e: Exception) {
                _uiState.value = UiState.Error(e.message)
            }
        }
    }
}

// Тест
class UserViewModelTest {
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()
    
    @Test
    fun `loadUser updates state to Success`() = runTest {
        // Given
        val repository = mockk<UserRepository>()
        val user = User("1", "John")
        coEvery { repository.getUser("1") } returns user
        
        val viewModel = UserViewModel(repository)
        
        // When
        viewModel.loadUser("1")
        
        // Then
        assertEquals(UiState.Success(user), viewModel.uiState.value)
    }
    
    @Test
    fun `loadUser updates state to Error on exception`() = runTest {
        // Given
        val repository = mockk<UserRepository>()
        coEvery { repository.getUser("1") } throws Exception("Network error")
        
        val viewModel = UserViewModel(repository)
        
        // When
        viewModel.loadUser("1")
        
        // Then
        val state = viewModel.uiState.value
        assertTrue(state is UiState.Error)
        assertEquals("Network error", (state as UiState.Error).message)
    }
}

// MainDispatcherRule для замены Main диспетчера в тестах
class MainDispatcherRule(
    private val testDispatcher: TestDispatcher = UnconfinedTestDispatcher()
) : TestWatcher() {
    override fun starting(description: Description) {
        Dispatchers.setMain(testDispatcher)
    }
    
    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
```

### 3. Тестирование Flow

```kotlin
class UserRepository(private val dao: UserDao) {
    fun observeUsers(): Flow<List<User>> = dao.observeUsers()
        .map { users -> users.filter { it.isActive } }
}

// Тест
class UserRepositoryFlowTest {
    @Test
    fun `observeUsers filters active users`() = runTest {
        // Given
        val dao = mockk<UserDao>()
        val users = listOf(
            User("1", "John", isActive = true),
            User("2", "Jane", isActive = false),
            User("3", "Bob", isActive = true)
        )
        every { dao.observeUsers() } returns flowOf(users)
        
        val repository = UserRepository(dao)
        
        // When
        val result = repository.observeUsers().first()
        
        // Then
        assertEquals(2, result.size)
        assertTrue(result.all { it.isActive })
    }
}
```

### 4. Тестирование с задержками (delay)

```kotlin
class DataRefresher {
    suspend fun refreshPeriodically() {
        while (true) {
            fetchData()
            delay(5000) // 5 секунд
        }
    }
    
    suspend fun fetchData() { /* ... */ }
}

// Тест
class DataRefresherTest {
    @Test
    fun `refreshPeriodically calls fetchData multiple times`() = runTest {
        // Given
        val refresher = spyk(DataRefresher())
        coEvery { refresher.fetchData() } returns Unit
        
        // When
        val job = launch {
            refresher.refreshPeriodically()
        }
        
        advanceTimeBy(15000) // Перемотка времени на 15 сек
        job.cancel()
        
        // Then
        coVerify(exactly = 3) { refresher.fetchData() } // 0s, 5s, 10s
    }
}
```

### 5. Тестирование с инъекцией диспетчера

```kotlin
class UserRepository(
    private val api: ApiService,
    private val dispatcher: CoroutineDispatcher = Dispatchers.IO
) {
    suspend fun getUser(id: String): User = withContext(dispatcher) {
        api.fetchUser(id)
    }
}

// Тест
class UserRepositoryTest {
    @Test
    fun `getUser uses injected dispatcher`() = runTest {
        // Given
        val api = mockk<ApiService>()
        val user = User("1", "John")
        coEvery { api.fetchUser("1") } returns user
        
        // Инъекция тестового диспетчера
        val repository = UserRepository(api, UnconfinedTestDispatcher())
        
        // When
        val result = repository.getUser("1")
        
        // Then
        assertEquals(user, result)
    }
}
```

### 6. Тестирование SharedFlow (события)

```kotlin
class EventViewModel : ViewModel() {
    private val _events = MutableSharedFlow<Event>()
    val events: SharedFlow<Event> = _events.asSharedFlow()
    
    fun onButtonClick() {
        viewModelScope.launch {
            _events.emit(Event.ShowToast("Clicked"))
        }
    }
}

// Тест
class EventViewModelTest {
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()
    
    @Test
    fun `onButtonClick emits ShowToast event`() = runTest {
        // Given
        val viewModel = EventViewModel()
        val events = mutableListOf<Event>()
        
        // Собираем события в фоне
        val job = launch(UnconfinedTestDispatcher()) {
            viewModel.events.collect { events.add(it) }
        }
        
        // When
        viewModel.onButtonClick()
        
        // Then
        assertEquals(1, events.size)
        assertTrue(events[0] is Event.ShowToast)
        
        job.cancel()
    }
}
```

### Ключевые инструменты для тестирования:

**runTest** - запускает тест с виртуальным временем  
**coEvery / coVerify** - mock suspend функций (MockK)  
**advanceTimeBy** - перемотка виртуального времени  
**UnconfinedTestDispatcher** - выполняет корутины немедленно  
**StandardTestDispatcher** - контролируемое выполнение  
**MainDispatcherRule** - замена Main диспетчера для тестов  

### Краткая шпаргалка:

```kotlin
// 1. Простой suspend тест
@Test
fun test() = runTest {
    val result = repository.getData()
    assertEquals(expected, result)
}

// 2. Mock suspend функции
coEvery { api.fetch() } returns data
coVerify { api.fetch() }

// 3. Тест с задержкой
advanceTimeBy(1000)

// 4. Инъекция диспетчера
class Repo(val dispatcher: CoroutineDispatcher = Dispatchers.IO)
val repo = Repo(UnconfinedTestDispatcher())

// 5. Тест Flow
val result = flow.first() // или .toList()

// 6. Тест StateFlow
assertEquals(expectedState, viewModel.uiState.value)
```

## Резюме ключевых моментов

1. **Корутины** - легковесные потоки для асинхронного кода
2. **suspend** функции могут приостанавливаться без блокировки потока
3. **Dispatchers** определяют, в каком потоке выполняется код
4. **Scope** управляет жизненным циклом корутин
5. **Job** и **SupervisorJob** для управления иерархией корутин
6. **Flow** - холодный поток для асинхронных данных
7. **StateFlow** - горячий поток для состояния UI
8. **SharedFlow** - горячий поток для событий
9. **repeatOnLifecycle** для безопасного сбора Flow в UI
10. **Structured Concurrency** - корутины привязаны к scope

Удачи на собеседовании! 🚀
