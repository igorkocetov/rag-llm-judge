# GoF Design Patterns для Mobile разработчика

## Что такое GoF?
**Gang of Four (Банда четырех)** - 4 автора книги "Design Patterns: Elements of Reusable Object-Oriented Software" (1994). Описали 23 паттерна проектирования.

## Классификация паттернов

### 1. Порождающие (Creational) - 5 паттернов
Отвечают за создание объектов.

### 2. Структурные (Structural) - 7 паттернов
Отвечают за композицию классов и объектов.

### 3. Поведенческие (Behavioral) - 11 паттернов
Отвечают за взаимодействие между объектами.

---

## Ключевые паттерны для Mobile

### ПОРОЖДАЮЩИЕ ПАТТЕРНЫ

#### 1. Factory (Фабрика) vs Factory Method (Фабричный метод)

**Factory (Simple Factory) - НЕ GoF паттерн!**
```kotlin
// Простая фабрика - один класс создает разные объекты
class NetworkClientFactory {
    fun create(type: String): NetworkClient {
        return when(type) {
            "REST" -> RestClient()
            "GRAPHQL" -> GraphQLClient()
            else -> throw IllegalArgumentException()
        }
    }
}

// Использование
val factory = NetworkClientFactory()
val client = factory.create("REST")
```

**Factory Method (Фабричный метод) - GoF паттерн**
```kotlin
// Абстрактный класс с фабричным методом
abstract class DataSource {
    // Фабричный метод - делегирует создание подклассам
    abstract fun createRepository(): Repository
    
    fun fetchData(): Data {
        val repo = createRepository() // используем фабричный метод
        return repo.getData()
    }
}

// Конкретные реализации
class LocalDataSource : DataSource() {
    override fun createRepository(): Repository = LocalRepository()
}

class RemoteDataSource : DataSource() {
    override fun createRepository(): Repository = RemoteRepository()
}

// Использование
val dataSource: DataSource = RemoteDataSource()
val data = dataSource.fetchData() // внутри создастся RemoteRepository
```

**КЛЮЧЕВАЯ РАЗНИЦА:**
- **Factory (Simple Factory)**: Один класс с методом, который создает объекты на основе параметра. Не является GoF паттерном.
- **Factory Method**: Определяет интерфейс для создания объекта, но позволяет подклассам решать, какой класс инстанцировать. Это GoF паттерн.

**В чем суть Factory Method?**
- Родительский класс объявляет абстрактный метод создания
- Подклассы переопределяют этот метод и создают конкретные объекты
- Клиентский код работает с абстракцией, не зная конкретного типа

---

#### 2. Abstract Factory
Создает семейства связанных объектов.

```kotlin
// Пример для Android: создание UI компонентов под разные темы
interface UIFactory {
    fun createButton(): Button
    fun createTextField(): TextField
}

class MaterialUIFactory : UIFactory {
    override fun createButton() = MaterialButton()
    override fun createTextField() = MaterialTextField()
}

class CupertinoUIFactory : UIFactory {
    override fun createButton() = CupertinoButton()
    override fun createTextField() = CupertinoTextField()
}
```

**Когда использовать в Mobile:**
- Создание UI для разных платформ (Android/iOS в KMP)
- Разные темы приложения (Material/Cupertino)
- Разные конфигурации (Dev/Prod окружения)

---

#### 3. Singleton
Гарантирует единственный экземпляр класса.

```kotlin
// Kotlin way - object это встроенный Singleton
object DatabaseManager {
    fun getConnection() { }
}

// Использование - просто обращаемся напрямую:
DatabaseManager.getConnection() // Инициализация не нужна!

// Thread-safe Java way (Double-Checked Locking)
class NetworkManager private constructor() {
    companion object {
        @Volatile // ОБЯЗАТЕЛЬНО! Гарантирует видимость изменений между потоками
        private var instance: NetworkManager? = null
        
        fun getInstance(): NetworkManager {
            // Double-Checked Locking: проверка → синхронизация → проверка
            return instance ?: synchronized(this) {
                instance ?: NetworkManager().also { instance = it }
            }
        }
    }
}

// Что делает @Volatile:
// - Запись в переменную сразу видна всем потокам
// - Чтение всегда из основной памяти, а не из CPU кэша
// - Без @Volatile поток B может не увидеть изменения от потока A
```

**Проблемы Singleton в Android:**
- Сложно тестировать (нельзя подменить mock)
- Может приводить к memory leaks (хранит Context)
- Нарушает Dependency Inversion Principle

**Лучше использовать DI (Hilt/Koin) с @Singleton scope**

---

#### 4. Builder
Пошаговое создание сложных объектов.

**Зачем Builder, если есть конструктор с параметрами?**

```kotlin
// ПРОБЛЕМА с конструктором:
class NetworkRequest(
    val url: String,
    val method: String = "GET",
    val headers: Map<String, String> = emptyMap(),
    val timeout: Long = 30000,
    val retryCount: Int = 3,
    val cacheEnabled: Boolean = true
)

// Неудобно при 10+ параметрах:
val req = NetworkRequest(
    url = "https://api.com",
    method = "POST",
    headers = emptyMap(),  // приходится указывать default
    timeout = 5000,
    retryCount = 3,        // default
    cacheEnabled = false   // меняем только это
)

// РЕШЕНИЕ - Builder:
class NetworkRequest private constructor(
    val url: String,
    val method: String,
    val headers: Map<String, String>,
    val timeout: Long
) {
    class Builder {
        private var url: String = ""
        private var method: String = "GET"
        private var headers: Map<String, String> = emptyMap()
        private var timeout: Long = 30000
        
        fun url(url: String) = apply { this.url = url }
        fun method(method: String) = apply { this.method = method }
        fun headers(headers: Map<String, String>) = apply { this.headers = headers }
        fun timeout(timeout: Long) = apply { this.timeout = timeout }
        
        fun build(): NetworkRequest {
            // Валидация перед созданием
            require(url.isNotEmpty()) { "URL required" }
            return NetworkRequest(url, method, headers, timeout)
        }
    }
}

// Использование - указываем только нужные параметры!
val request = NetworkRequest.Builder()
    .url("https://api.example.com")
    .method("POST")
    .timeout(5000)
    // headers пропускаем - используется default
    .build()
```

**Преимущества Builder:**
1. **Необязательные параметры** - указываем только то, что нужно
2. **Читаемость** - `.timeout(5000)` понятнее чем просто `5000`
3. **Валидация** - проверка в `build()` перед созданием объекта
4. **Immutability** - объект создается с `val`, нельзя изменить
5. **Fluent interface** - цепочка вызовов `.method1().method2()`

**Примеры в Android:**
- `AlertDialog.Builder()`
- `Notification.Builder()`
- `Retrofit.Builder()`
- `Room.databaseBuilder()`

---

#### 5. Prototype
Клонирование объектов.

```kotlin
interface Prototype {
    fun clone(): Prototype
}

data class UserProfile(
    val name: String,
    val settings: MutableList<String>
) : Prototype {
    override fun clone(): UserProfile {
        return copy(settings = settings.toMutableList())
    }
}
```

**В Kotlin:** data classes с `copy()` - это реализация Prototype.

---

### СТРУКТУРНЫЕ ПАТТЕРНЫ

#### 6. Facade (Фасад) vs Decorator (Декоратор)

**Facade (Фасад)**
```kotlin
// Сложная подсистема
class OrderRepository { fun createOrder(order: Order) { } }
class PaymentService { fun processPayment(orderId: String) { } }
class NotificationService { fun notifyUser(userId: String, message: String) { } }
class InventoryService { fun updateStock(productId: String) { } }

// ФАСАД - упрощает интерфейс сложной подсистемы
class OrderFacade(
    private val orderRepo: OrderRepository,
    private val paymentService: PaymentService,
    private val notificationService: NotificationService,
    private val inventoryService: InventoryService
) {
    // Один простой метод вместо 4 вызовов
    fun placeOrder(order: Order, userId: String) {
        orderRepo.createOrder(order)
        paymentService.processPayment(order.id)
        inventoryService.updateStock(order.productId)
        notificationService.notifyUser(userId, "Order placed!")
    }
}

// Использование
val facade = OrderFacade(orderRepo, payment, notification, inventory)
facade.placeOrder(order, userId) // Один вызов вместо четырех!
```

**Decorator (Декоратор)**
```kotlin
// Базовый интерфейс
interface Coffee {
    fun cost(): Double
    fun description(): String
}

// Базовая реализация
class SimpleCoffee : Coffee {
    override fun cost() = 5.0
    override fun description() = "Simple coffee"
}

// ДЕКОРАТОР - добавляет функциональность динамически
abstract class CoffeeDecorator(private val coffee: Coffee) : Coffee {
    override fun cost() = coffee.cost()
    override fun description() = coffee.description()
}

class MilkDecorator(coffee: Coffee) : CoffeeDecorator(coffee) {
    override fun cost() = super.cost() + 1.5
    override fun description() = super.description() + ", milk"
}

class SugarDecorator(coffee: Coffee) : CoffeeDecorator(coffee) {
    override fun cost() = super.cost() + 0.5
    override fun description() = super.description() + ", sugar"
}

// Использование - оборачиваем объект в декораторы
var coffee: Coffee = SimpleCoffee()
coffee = MilkDecorator(coffee)
coffee = SugarDecorator(coffee)
println("${coffee.description()} costs ${coffee.cost()}") 
// "Simple coffee, milk, sugar costs 7.0"
```

**КЛЮЧЕВАЯ РАЗНИЦА:**

| Аспект | Facade | Decorator |
|--------|--------|-----------|
| **Цель** | Упростить сложный интерфейс | Добавить функциональность |
| **Структура** | Один фасад → много подсистем | Декоратор оборачивает один объект |
| **Интерфейс** | Создает НОВЫЙ упрощенный интерфейс | Сохраняет ТОТ ЖЕ интерфейс |
| **Количество объектов** | Работает с несколькими объектами | Работает с одним объектом |
| **Динамичность** | Статичен | Динамически добавляет поведение |
| **Решает SRP?** | ❌ НЕТ | ❌ НЕТ |

**⚠️ ВАЖНО: Facade НЕ решает проблему SRP!**

Facade используется для **упрощения сложного интерфейса**, а НЕ для исправления нарушения SRP.

**Для исправления SRP используется простое разделение классов:**

```kotlin
// ❌ НАРУШЕНИЕ SRP
class Order {
    fun createOrder() { }
    fun notifyUser() { } // Не относится к Order!
}

// ✅ ПРАВИЛЬНО - разделяем ответственность
class OrderRepository {
    fun createOrder(order: OrderData) { }
}

class NotificationService {
    fun notifyUser(userId: String, message: String) { }
}

// Координатор (это НЕ Facade, просто композиция!)
class OrderService(
    private val orderRepo: OrderRepository,
    private val notificationService: NotificationService
) {
    fun placeOrder(order: OrderData) {
        orderRepo.createOrder(order)
        notificationService.notifyUser(order.userId, "Order created")
    }
}
```

**Разница:**
- **Композиция для SRP**: 2-3 простых класса, каждый делает одно дело
- **Facade**: 4+ сложных подсистемы (каждая с множеством методов), фасад упрощает работу с ними

**Примеры в Android:**
- **Facade**: `MediaPlayer` (скрывает сложность аудио/видео), `Context` (фасад для системных сервисов)
- **Decorator**: `BufferedInputStream(FileInputStream())`, `ContextWrapper`

---

#### 7. Adapter
Преобразует интерфейс одного класса в другой.

```kotlin
// Старый интерфейс
interface OldPaymentGateway {
    fun pay(amount: Int)
}

// Новый интерфейс
interface NewPaymentProcessor {
    fun processPayment(amount: Double, currency: String)
}

// АДАПТЕР
class PaymentAdapter(private val oldGateway: OldPaymentGateway) : NewPaymentProcessor {
    override fun processPayment(amount: Double, currency: String) {
        oldGateway.pay(amount.toInt()) // адаптируем вызов
    }
}
```

**В Android:**
- `RecyclerView.Adapter` - адаптирует данные к View
- `ArrayAdapter`, `CursorAdapter`

---

#### 8. Proxy
Контролирует доступ к объекту.

```kotlin
interface Image {
    fun display()
}

class RealImage(private val filename: String) : Image {
    init {
        loadFromDisk() // тяжелая операция
    }
    
    private fun loadFromDisk() {
        println("Loading $filename")
    }
    
    override fun display() {
        println("Displaying $filename")
    }
}

// PROXY - ленивая загрузка
class ImageProxy(private val filename: String) : Image {
    private var realImage: RealImage? = null
    
    override fun display() {
        if (realImage == null) {
            realImage = RealImage(filename) // загружаем только при первом вызове
        }
        realImage?.display()
    }
}
```

**Типы Proxy:**
- **Virtual Proxy** - ленивая инициализация (пример выше)
- **Protection Proxy** - контроль доступа
- **Remote Proxy** - работа с удаленными объектами (Retrofit)

---

#### 9. Composite
Древовидная структура объектов.

```kotlin
interface UIComponent {
    fun render()
}

class Button(private val text: String) : UIComponent {
    override fun render() = println("Button: $text")
}

class Panel : UIComponent {
    private val children = mutableListOf<UIComponent>()
    
    fun add(component: UIComponent) {
        children.add(component)
    }
    
    override fun render() {
        println("Panel:")
        children.forEach { it.render() }
    }
}

// Использование
val panel = Panel()
panel.add(Button("OK"))
panel.add(Button("Cancel"))
panel.render()
```

**В Android:** View hierarchy - `ViewGroup` содержит `View`

---

### ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ

#### 10. Observer
Подписка на изменения объекта.

```kotlin
interface Observer {
    fun update(data: String)
}

class Subject {
    private val observers = mutableListOf<Observer>()
    
    fun attach(observer: Observer) {
        observers.add(observer)
    }
    
    fun notify(data: String) {
        observers.forEach { it.update(data) }
    }
}
```

**В Android:**
- `LiveData.observe()`
- `Flow.collect()`
- `RxJava.subscribe()`
- `View.setOnClickListener()`

---

#### 11. Strategy
Инкапсуляция алгоритмов.

```kotlin
interface SortStrategy {
    fun sort(list: List<Int>): List<Int>
}

class QuickSort : SortStrategy {
    override fun sort(list: List<Int>) = list.sorted() // упрощенно
}

class BubbleSort : SortStrategy {
    override fun sort(list: List<Int>) = list.sortedDescending() // упрощенно
}

class Sorter(private var strategy: SortStrategy) {
    fun setStrategy(strategy: SortStrategy) {
        this.strategy = strategy
    }
    
    fun sort(list: List<Int>) = strategy.sort(list)
}
```

**В Android:**
- `LayoutManager` в RecyclerView (LinearLayoutManager, GridLayoutManager)
- `Interpolator` для анимаций

---

#### 12. Command
Инкапсуляция запроса как объекта.

```kotlin
interface Command {
    fun execute()
    fun undo()
}

class CopyCommand(private val editor: TextEditor) : Command {
    private var backup: String = ""
    
    override fun execute() {
        backup = editor.text
        editor.clipboard = editor.getSelection()
    }
    
    override fun undo() {
        editor.text = backup
    }
}

class CommandInvoker {
    private val history = mutableListOf<Command>()
    
    fun execute(command: Command) {
        command.execute()
        history.add(command)
    }
    
    fun undo() {
        history.removeLastOrNull()?.undo()
    }
}
```

**В Android:**
- Undo/Redo функциональность
- `Runnable` в Handler

---

#### 13. State
Изменение поведения объекта при изменении состояния.

```kotlin
interface PlayerState {
    fun play(player: MusicPlayer)
    fun pause(player: MusicPlayer)
}

class PlayingState : PlayerState {
    override fun play(player: MusicPlayer) {
        println("Already playing")
    }
    override fun pause(player: MusicPlayer) {
        println("Pausing...")
        player.state = PausedState()
    }
}

class PausedState : PlayerState {
    override fun play(player: MusicPlayer) {
        println("Resuming...")
        player.state = PlayingState()
    }
    override fun pause(player: MusicPlayer) {
        println("Already paused")
    }
}

class MusicPlayer {
    var state: PlayerState = PausedState()
    
    fun play() = state.play(this)
    fun pause() = state.pause(this)
}
```

**В Android:** Lifecycle states (Created, Started, Resumed)

---

#### 14. Template Method
Определяет скелет алгоритма.

```kotlin
abstract class DataLoader {
    // Template method
    fun loadData() {
        openConnection()
        fetchData()
        parseData()
        closeConnection()
    }
    
    protected abstract fun openConnection()
    protected abstract fun fetchData()
    protected abstract fun parseData()
    protected abstract fun closeConnection()
}

class DatabaseLoader : DataLoader() {
    override fun openConnection() = println("Open DB connection")
    override fun fetchData() = println("SQL query")
    override fun parseData() = println("Parse rows")
    override fun closeConnection() = println("Close DB")
}
```

---

#### 15. Chain of Responsibility
Цепочка обработчиков.

```kotlin
abstract class Handler {
    var next: Handler? = null
    
    fun handle(request: Request) {
        if (canHandle(request)) {
            process(request)
        } else {
            next?.handle(request)
        }
    }
    
    protected abstract fun canHandle(request: Request): Boolean
    protected abstract fun process(request: Request)
}

class AuthHandler : Handler() {
    override fun canHandle(request: Request) = !request.isAuthenticated
    override fun process(request: Request) {
        println("Authenticating...")
        request.isAuthenticated = true
        next?.handle(request)
    }
}
```

**В Android:** 
- Touch event handling (View → ViewGroup → Activity)
- Interceptor chain в OkHttp

---

## Ответ на ваш вопрос про Facade

**Вы НЕ совсем правы** в понимании Facade и его связи с SOLID.

### Ваш пример:
```kotlin
class Order { fun create() {} }
class UserNotification { fun notify() {} }
class FullOrder {
    fun createFullOrder() {
        Order().create()
        UserNotification().notify()
    }
}
```

**Проблемы с вашим пониманием:**

1. **Это НЕ решает проблему S (Single Responsibility)**
   - Наоборот, `FullOrder` НАРУШАЕТ SRP, потому что отвечает за 2 вещи: создание заказа И уведомление
   - SRP говорит: один класс = одна причина для изменения
   - Если изменится логика уведомлений, придется менять `FullOrder`

2. **Facade НЕ для решения SRP**
   - Facade используется для **упрощения сложного интерфейса**
   - Он предоставляет простой интерфейс к сложной подсистеме
   - Цель: удобство использования, а не разделение ответственности

### Правильное понимание:

**Facade в вашем случае:**
```kotlin
// Сложная подсистема (много классов, много методов)
class OrderRepository {
    fun validateOrder(order: Order): Boolean { }
    fun saveOrder(order: Order): String { }
    fun updateInventory(orderId: String) { }
}

class PaymentService {
    fun initializePayment(amount: Double): String { }
    fun processPayment(paymentId: String): Boolean { }
    fun refund(paymentId: String) { }
}

class NotificationService {
    fun sendEmail(email: String, message: String) { }
    fun sendPush(userId: String, message: String) { }
    fun sendSMS(phone: String, message: String) { }
}

class AnalyticsService {
    fun trackEvent(event: String) { }
    fun trackPurchase(orderId: String, amount: Double) { }
}

// ФАСАД - упрощает работу с этой сложной системой
class OrderFacade(
    private val orderRepo: OrderRepository,
    private val paymentService: PaymentService,
    private val notificationService: NotificationService,
    private val analyticsService: AnalyticsService
) {
    // Один простой метод вместо 7+ вызовов
    fun placeOrder(order: Order, user: User): Result<String> {
        // Клиенту не нужно знать про все эти шаги
        if (!orderRepo.validateOrder(order)) {
            return Result.failure(Exception("Invalid order"))
        }
        
        val orderId = orderRepo.saveOrder(order)
        val paymentId = paymentService.initializePayment(order.amount)
        
        if (!paymentService.processPayment(paymentId)) {
            return Result.failure(Exception("Payment failed"))
        }
        
        orderRepo.updateInventory(orderId)
        notificationService.sendEmail(user.email, "Order confirmed!")
        notificationService.sendPush(user.id, "Order #$orderId")
        analyticsService.trackPurchase(orderId, order.amount)
        
        return Result.success(orderId)
    }
}

// Использование - ПРОСТО!
val facade = OrderFacade(orderRepo, payment, notification, analytics)
val result = facade.placeOrder(order, user) // Один вызов!
```

**Ключевые моменты:**
- Facade **упрощает** сложный интерфейс (много классов → один метод)
- Facade **не нарушает** SRP - каждый класс делает свое
- Facade **скрывает** сложность подсистемы от клиента
- Клиент работает с фасадом, а не с 4 разными сервисами

**Для решения SRP используется:**
- Разделение классов по ответственности (Order, Notification - разные классы)
- Dependency Injection
- Composition over Inheritance

---

## Топ-10 паттернов для Mobile собеседования

1. **Singleton** - DI контейнеры, репозитории
2. **Factory Method** - создание объектов в зависимости от условий
3. **Builder** - создание сложных объектов (Retrofit, Room)
4. **Observer** - LiveData, Flow, RxJava
5. **Adapter** - RecyclerView.Adapter
6. **Facade** - упрощение сложных API
7. **Decorator** - добавление функциональности (Streams)
8. **Strategy** - LayoutManager, сортировки
9. **Repository** - НЕ GoF, но важен для Android (Clean Architecture)
10. **MVVM/MVI** - НЕ GoF, но архитектурные паттерны для UI

---

## Частые вопросы на собеседовании

### 1. Какие паттерны используются в Android SDK?
- **Builder**: AlertDialog.Builder, Notification.Builder
- **Singleton**: Application context
- **Adapter**: RecyclerView.Adapter, ArrayAdapter
- **Observer**: LiveData, ContentObserver
- **Factory**: LayoutInflater.from()
- **Facade**: Context (доступ к системным сервисам)
- **Proxy**: Binder (IPC)
- **Composite**: View hierarchy

### 2. Проблемы Singleton в Android?

#### a) Memory leaks (хранение Context)
```kotlin
// ❌ ОПАСНО - утечка памяти!
object DatabaseManager {
    private var context: Context? = null
    
    fun init(context: Context) {
        this.context = context // Singleton живет вечно, Context не освобождается!
    }
}
```

#### b) Сложность тестирования
```kotlin
// ❌ Невозможно подменить на mock
object NetworkManager {
    fun fetchData(): String = "real data"
}

class UserRepository {
    fun getUser(): User {
        val data = NetworkManager.fetchData() // Жестко привязаны к Singleton!
        // В тестах ВСЕГДА будет вызываться реальный NetworkManager
        return parseUser(data)
    }
}

// Тест - ПРОБЛЕМА!
@Test
fun testGetUser() {
    // Как подменить NetworkManager на mock? НИКАК!
    val repo = UserRepository()
    val user = repo.getUser() // Вызовет реальный network запрос
}
```

#### c) **Нарушение DIP (Dependency Inversion Principle)**

**DIP гласит:**
- Модули верхнего уровня НЕ должны зависеть от модулей нижнего уровня
- Оба должны зависеть от **абстракций** (интерфейсов)
- Абстракции НЕ должны зависеть от деталей

**Проблема Singleton:**

```kotlin
// ❌ НАРУШЕНИЕ DIP - зависимость от конкретной реализации
object DatabaseManager {
    fun saveUser(user: User) {
        println("Saving to SQLite: $user")
    }
}

class UserRepository {
    fun createUser(user: User) {
        // ЖЕСТКАЯ зависимость от конкретного класса DatabaseManager!
        // Зависим от ДЕТАЛЕЙ реализации, а не от абстракции
        DatabaseManager.saveUser(user)
    }
}

// Проблемы:
// 1. Невозможно заменить DatabaseManager на другую реализацию
// 2. Невозможно протестировать с mock
// 3. Нарушен DIP - зависим от конкретного класса, а не интерфейса
```

**✅ ПРАВИЛЬНО - следуем DIP с помощью DI:**

```kotlin
// Абстракция (интерфейс)
interface UserStorage {
    fun saveUser(user: User)
}

// Конкретная реализация
class SQLiteUserStorage : UserStorage {
    override fun saveUser(user: User) {
        println("Saving to SQLite: $user")
    }
}

// Другая реализация
class InMemoryUserStorage : UserStorage {
    override fun saveUser(user: User) {
        println("Saving to memory: $user")
    }
}

// Repository зависит от АБСТРАКЦИИ, а не от конкретного класса!
class UserRepository(
    private val storage: UserStorage // Зависимость от интерфейса!
) {
    fun createUser(user: User) {
        storage.saveUser(user) // Не знаем конкретную реализацию
    }
}

// Использование - внедряем зависимость извне
val repository = UserRepository(SQLiteUserStorage())

// Тестирование - легко подменить на mock!
@Test
fun testCreateUser() {
    val mockStorage = InMemoryUserStorage() // или Mockk
    val repository = UserRepository(mockStorage)
    repository.createUser(user)
    // Проверяем mock
}
```

**Почему Singleton нарушает DIP:**

| Аспект | Singleton | DI с интерфейсом |
|--------|-----------|------------------|
| **Зависимость** | От конкретного класса | От абстракции (интерфейса) |
| **Связанность** | Жесткая (tight coupling) | Слабая (loose coupling) |
| **Тестирование** | Невозможно подменить | Легко подменить mock |
| **Гибкость** | Нельзя заменить реализацию | Можно менять реализацию |
| **DIP** | ❌ Нарушает | ✅ Соблюдает |

**Решение: DI с @Singleton scope**

```kotlin
// Hilt/Dagger
@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides
    @Singleton // Scope - один экземпляр, но через DI!
    fun provideUserStorage(): UserStorage {
        return SQLiteUserStorage()
    }
}

// Внедрение через конструктор
class UserRepository @Inject constructor(
    private val storage: UserStorage // Зависимость от интерфейса!
) {
    fun createUser(user: User) {
        storage.saveUser(user)
    }
}

// Преимущества:
// ✅ Один экземпляр (как Singleton)
// ✅ Зависимость от интерфейса (соблюдаем DIP)
// ✅ Легко тестировать (можем подменить)
// ✅ Гибкость (можем изменить реализацию в модуле)
```

### 3. Когда использовать Decorator vs Inheritance?
- **Decorator**: динамическое добавление функциональности, комбинации
- **Inheritance**: статическая иерархия, IS-A отношение

### 4. Разница Observer vs Pub/Sub?
- **Observer**: Subject знает про Observers
- **Pub/Sub**: Publisher и Subscriber не знают друг о друге (Event Bus)

---

## Антипаттерны (чего избегать)

1. **God Object** - класс делает слишком много
2. **Spaghetti Code** - запутанный код без структуры
3. **Lava Flow** - мертвый код, который боятся удалить
4. **Golden Hammer** - использование одного паттерна везде
5. **Singleton Overuse** - синглтоны везде вместо DI

---

## Когда НЕ использовать паттерны?

- Простая задача не требует сложного решения
- Паттерн усложняет код без выгоды
- Команда не знакома с паттерном
- **YAGNI** (You Aren't Gonna Need It) - не добавляй то, что может понадобиться

**Правило:** Паттерны - это инструменты, а не цель. Используй когда решают реальную проблему.
