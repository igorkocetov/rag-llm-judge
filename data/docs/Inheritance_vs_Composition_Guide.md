# Наследование vs Композиция - Глубокий Разбор для Интервью

## 📋 Содержание
1. [Проблемы Наследования](#проблемы-наследования)
2. [Композиция как Решение](#композиция-как-решение)
3. [Наследование vs Композиция](#наследование-vs-композиция)
4. [Dependency Injection и Композиция](#dependency-injection-и-композиция)
5. [@Volatile - Что Это На Самом Деле](#volatile---что-это-на-самом-деле)
6. [Практические Примеры](#практические-примеры)

---

## Проблемы Наследования

### Почему Наследование Считается Плохим?

**Основные проблемы:**

#### 1. **Жесткая Связанность (Tight Coupling)**

```kotlin
// ❌ ПРОБЛЕМА: Наследник жестко привязан к родителю
open class Vehicle {
    open fun start() {
        checkFuel()
        igniteEngine()
        println("Vehicle started")
    }
    
    private fun checkFuel() { /* ... */ }
    private fun igniteEngine() { /* ... */ }
}

class Car : Vehicle() {
    override fun start() {
        // Мы ОБЯЗАНЫ вызвать super.start() или переписать всю логику
        super.start()
        // Что если в Vehicle изменится логика start()?
        // Наш Car сломается!
    }
}

// Проблема: Car знает ВСЮ внутреннюю кухню Vehicle
// Изменение в Vehicle может сломать Car
```

#### 2. **Хрупкий Базовый Класс (Fragile Base Class Problem)**

```kotlin
// ❌ ПРОБЛЕМА: Изменение родителя ломает наследников
open class Counter {
    private var count = 0
    
    open fun add(value: Int) {
        count += value
    }
    
    open fun addAll(values: List<Int>) {
        values.forEach { add(it) }  // Использует add()
    }
    
    fun getCount() = count
}

class InstrumentedCounter : Counter() {
    var addCount = 0
    
    override fun add(value: Int) {
        addCount++  // Считаем вызовы
        super.add(value)
    }
    
    override fun addAll(values: List<Int>) {
        addCount += values.size  // Считаем элементы
        super.addAll(values)  // ❌ БАГ! add() вызовется еще раз
    }
}

fun main() {
    val counter = InstrumentedCounter()
    counter.addAll(listOf(1, 2, 3))
    println(counter.addCount)  // Ожидаем 3, получаем 6!
    // addAll вызвал add() 3 раза, каждый раз увеличивая addCount
}

// Проблема: Мы не контролируем, как родитель использует методы
// Изменение реализации в родителе ломает наследника
```

#### 3. **Нарушение Принципа Подстановки Барбары Лисков (LSP)**

```kotlin
// ❌ ПРОБЛЕМА: Квадрат НЕ является прямоугольником в ООП
open class Rectangle(
    open var width: Int,
    open var height: Int
) {
    open fun area() = width * height
}

class Square(size: Int) : Rectangle(size, size) {
    override var width: Int
        get() = super.width
        set(value) {
            super.width = value
            super.height = value  // Меняем оба!
        }
    
    override var height: Int
        get() = super.height
        set(value) {
            super.width = value  // Меняем оба!
            super.height = value
        }
}

fun testRectangle(rect: Rectangle) {
    rect.width = 5
    rect.height = 10
    println("Expected area: 50, actual: ${rect.area()}")
}

fun main() {
    testRectangle(Rectangle(0, 0))  // 50 ✅
    testRectangle(Square(0))        // 100 ❌ Нарушение LSP!
}

// Проблема: Square не может корректно заменить Rectangle
// "is-a" отношение не работает в коде, хотя работает в математике
```

#### 4. **Невозможность Изменить Поведение в Runtime**

```kotlin
// ❌ ПРОБЛЕМА: Поведение фиксировано на этапе компиляции
open class Logger {
    open fun log(message: String) {
        println(message)
    }
}

class FileLogger : Logger() {
    override fun log(message: String) {
        // Пишем в файл
    }
}

class DatabaseLogger : Logger() {
    override fun log(message: String) {
        // Пишем в БД
    }
}

// Проблема: Нельзя изменить тип логгера в runtime
// Нужно создавать новый объект
fun main() {
    var logger: Logger = FileLogger()
    logger.log("Message")
    
    // Хотим переключиться на DatabaseLogger
    logger = DatabaseLogger()  // Создаем НОВЫЙ объект!
    // Теряем состояние предыдущего логгера
}
```

#### 5. **Ограничения Множественного Наследования**

```kotlin
// ❌ ПРОБЛЕМА: Нельзя унаследоваться от нескольких классов
open class Flyable {
    fun fly() { println("Flying") }
}

open class Swimmable {
    fun swim() { println("Swimming") }
}

// ❌ ОШИБКА: Множественное наследование запрещено
// class Duck : Flyable(), Swimmable()

// Приходится выбирать:
class Duck : Flyable() {
    // Теряем swim()
}

// Или дублировать код:
class Duck2 {
    fun fly() { println("Flying") }   // Дубликат
    fun swim() { println("Swimming") } // Дубликат
}
```

#### 6. **Нарушение Инкапсуляции**

```kotlin
// ❌ ПРОБЛЕМА: Наследник получает доступ к внутренностям родителя
open class BankAccount(
    protected var balance: Double  // protected - доступен наследникам
) {
    open fun withdraw(amount: Double) {
        if (balance >= amount) {
            balance -= amount
        }
    }
}

class HackedAccount(balance: Double) : BankAccount(balance) {
    fun stealMoney() {
        // Прямой доступ к balance!
        balance = 1_000_000.0  // ❌ Обошли всю логику
    }
}

// Проблема: protected нарушает инкапсуляцию
// Наследник может обойти бизнес-логику родителя
```

#### 7. **Глубокие Иерархии - Сложность Понимания**

```kotlin
// ❌ ПРОБЛЕМА: Сложно понять, что делает класс
open class A {
    open fun method1() { /* ... */ }
}

open class B : A() {
    override fun method1() { super.method1(); /* ... */ }
    open fun method2() { /* ... */ }
}

open class C : B() {
    override fun method1() { super.method1(); /* ... */ }
    override fun method2() { super.method2(); /* ... */ }
    open fun method3() { /* ... */ }
}

class D : C() {
    override fun method1() { super.method1(); /* ... */ }
    override fun method2() { super.method2(); /* ... */ }
    override fun method3() { super.method3(); /* ... */ }
    
    // Чтобы понять, что делает method1(), нужно прочитать
    // реализацию в D, C, B, A - 4 класса!
}

// Проблема: Глубокая иерархия = высокая когнитивная нагрузка
```

### Когда Наследование Оправдано?

```kotlin
// ✅ ХОРОШО: Истинное "is-a" отношение
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val exception: Exception) : Result<Nothing>()
}

// ✅ ХОРОШО: Расширение функциональности библиотечного класса
class CustomView : View {
    constructor(context: Context) : super(context)
    // Добавляем свою логику
}

// ✅ ХОРОШО: Шаблонный метод (Template Method Pattern)
abstract class DataProcessor {
    fun process() {
        loadData()
        validateData()
        transformData()
        saveData()
    }
    
    protected abstract fun loadData()
    protected abstract fun validateData()
    protected abstract fun transformData()
    protected abstract fun saveData()
}
```

---

## Композиция как Решение

### Что Такое Композиция?

**Композиция = "has-a" отношение**

Вместо наследования поведения, мы **делегируем** его другим объектам.

### Основные Преимущества

#### 1. **Слабая Связанность (Loose Coupling)**

```kotlin
// ✅ КОМПОЗИЦИЯ: Слабая связь через интерфейс
interface Engine {
    fun start()
    fun stop()
}

class PetrolEngine : Engine {
    override fun start() = println("Petrol engine started")
    override fun stop() = println("Petrol engine stopped")
}

class ElectricEngine : Engine {
    override fun start() = println("Electric engine started")
    override fun stop() = println("Electric engine stopped")
}

class Car(
    private val engine: Engine  // Композиция через интерфейс
) {
    fun start() {
        println("Car starting...")
        engine.start()  // Делегируем работу
        println("Car started!")
    }
    
    fun stop() {
        println("Car stopping...")
        engine.stop()
        println("Car stopped!")
    }
}

fun main() {
    val petrolCar = Car(PetrolEngine())
    petrolCar.start()
    
    val electricCar = Car(ElectricEngine())
    electricCar.start()
}

// Преимущество: Car не знает деталей реализации Engine
// Можем легко заменить Engine на другую реализацию
```

#### 2. **Гибкость в Runtime**

```kotlin
// ✅ КОМПОЗИЦИЯ: Можем менять поведение в runtime
interface PaymentStrategy {
    fun pay(amount: Double)
}

class CreditCardPayment : PaymentStrategy {
    override fun pay(amount: Double) = println("Paid $amount with credit card")
}

class PayPalPayment : PaymentStrategy {
    override fun pay(amount: Double) = println("Paid $amount with PayPal")
}

class CryptoPayment : PaymentStrategy {
    override fun pay(amount: Double) = println("Paid $amount with crypto")
}

class ShoppingCart {
    private var paymentStrategy: PaymentStrategy? = null
    
    fun setPaymentMethod(strategy: PaymentStrategy) {
        paymentStrategy = strategy
    }
    
    fun checkout(amount: Double) {
        paymentStrategy?.pay(amount) 
            ?: println("Please select payment method")
    }
}

fun main() {
    val cart = ShoppingCart()
    
    cart.setPaymentMethod(CreditCardPayment())
    cart.checkout(100.0)  // Credit card
    
    // Меняем метод оплаты в runtime!
    cart.setPaymentMethod(PayPalPayment())
    cart.checkout(200.0)  // PayPal
    
    cart.setPaymentMethod(CryptoPayment())
    cart.checkout(300.0)  // Crypto
}

// Преимущество: Гибкость без создания новых объектов
```

#### 3. **Множественное Поведение**

```kotlin
// ✅ КОМПОЗИЦИЯ: Можем комбинировать несколько поведений
interface Flyable {
    fun fly()
}

interface Swimmable {
    fun swim()
}

interface Walkable {
    fun walk()
}

class FlyingAbility : Flyable {
    override fun fly() = println("Flying in the sky")
}

class SwimmingAbility : Swimmable {
    override fun swim() = println("Swimming in water")
}

class WalkingAbility : Walkable {
    override fun walk() = println("Walking on ground")
}

// Duck может летать И плавать
class Duck(
    private val flyable: Flyable,
    private val swimmable: Swimmable
) {
    fun performFly() = flyable.fly()
    fun performSwim() = swimmable.swim()
}

// Penguin может плавать И ходить (но не летать)
class Penguin(
    private val swimmable: Swimmable,
    private val walkable: Walkable
) {
    fun performSwim() = swimmable.swim()
    fun performWalk() = walkable.walk()
}

fun main() {
    val duck = Duck(FlyingAbility(), SwimmingAbility())
    duck.performFly()   // ✅
    duck.performSwim()  // ✅
    
    val penguin = Penguin(SwimmingAbility(), WalkingAbility())
    penguin.performSwim()  // ✅
    penguin.performWalk()  // ✅
    // penguin.performFly() // ❌ Нет такого метода - правильно!
}

// Преимущество: Гибкое комбинирование поведений
```

#### 4. **Легкость Тестирования**

```kotlin
// ✅ КОМПОЗИЦИЯ: Легко мокировать зависимости
interface UserRepository {
    fun getUser(id: String): User?
}

interface Logger {
    fun log(message: String)
}

data class User(val id: String, val name: String)

class UserService(
    private val repository: UserRepository,
    private val logger: Logger
) {
    fun getUserName(id: String): String? {
        logger.log("Fetching user $id")
        val user = repository.getUser(id)
        logger.log("User fetched: ${user?.name}")
        return user?.name
    }
}

// Тестирование с моками
class FakeUserRepository : UserRepository {
    override fun getUser(id: String) = User(id, "Test User")
}

class FakeLogger : Logger {
    val logs = mutableListOf<String>()
    override fun log(message: String) {
        logs.add(message)
    }
}

fun testUserService() {
    val fakeRepo = FakeUserRepository()
    val fakeLogger = FakeLogger()
    val service = UserService(fakeRepo, fakeLogger)
    
    val name = service.getUserName("123")
    
    assert(name == "Test User")
    assert(fakeLogger.logs.size == 2)
    println("Test passed! ✅")
}

// Преимущество: Можем подменить любую зависимость для тестов
```

---

## Наследование vs Композиция

### Ключевое Различие

**Интервьюируемый сказал:**
> "При композиции мы можем расширить функционал класса не изменяя его, а при наследовании меняем функционал класса"

**Это НЕПРАВИЛЬНО!** Вот правильное объяснение:

### Правильное Объяснение

```kotlin
// НАСЛЕДОВАНИЕ = "IS-A" (является)
// Наследник ЯВЛЯЕТСЯ родителем
class Dog : Animal() {
    // Dog IS-A Animal
}

// КОМПОЗИЦИЯ = "HAS-A" (имеет)
// Класс ИМЕЕТ другой класс как часть
class Car(
    private val engine: Engine  // Car HAS-A Engine
)
```

### Детальное Сравнение

#### Пример 1: Расширение Функциональности

```kotlin
// ❌ НАСЛЕДОВАНИЕ: Изменяем класс изнутри
open class BasicLogger {
    open fun log(message: String) {
        println(message)
    }
}

class TimestampedLogger : BasicLogger() {
    override fun log(message: String) {
        // ИЗМЕНЯЕМ поведение родителя
        val timestamp = System.currentTimeMillis()
        super.log("[$timestamp] $message")
    }
}

// Проблемы:
// 1. Жестко привязаны к BasicLogger
// 2. Нельзя изменить в runtime
// 3. Нельзя комбинировать с другими логгерами

// ✅ КОМПОЗИЦИЯ: Расширяем без изменения
interface Logger {
    fun log(message: String)
}

class BasicLogger : Logger {
    override fun log(message: String) {
        println(message)
    }
}

class TimestampedLogger(
    private val logger: Logger  // Композиция
) : Logger {
    override fun log(message: String) {
        val timestamp = System.currentTimeMillis()
        logger.log("[$timestamp] $message")  // Делегируем
    }
}

class PrefixedLogger(
    private val logger: Logger,
    private val prefix: String
) : Logger {
    override fun log(message: String) {
        logger.log("$prefix: $message")
    }
}

fun main() {
    // Можем комбинировать!
    val logger = TimestampedLogger(
        PrefixedLogger(
            BasicLogger(),
            "APP"
        )
    )
    
    logger.log("Hello")
    // Вывод: [1234567890] APP: Hello
}

// Преимущества композиции:
// 1. Можем комбинировать декораторы
// 2. Можем менять в runtime
// 3. Не изменяем исходный класс
```

#### Пример 2: Принцип Open/Closed

```kotlin
// ❌ НАСЛЕДОВАНИЕ: Нарушает Open/Closed Principle
open class Report {
    open fun generate(): String {
        return "Basic Report"
    }
}

// Чтобы добавить PDF экспорт, нужно ИЗМЕНИТЬ иерархию
class PDFReport : Report() {
    override fun generate(): String {
        return "PDF: ${super.generate()}"
    }
}

// Чтобы добавить Excel, снова ИЗМЕНЯЕМ
class ExcelReport : Report() {
    override fun generate(): String {
        return "Excel: ${super.generate()}"
    }
}

// ✅ КОМПОЗИЦИЯ: Соблюдает Open/Closed Principle
interface ReportGenerator {
    fun generate(): String
}

interface ReportExporter {
    fun export(content: String): String
}

class BasicReportGenerator : ReportGenerator {
    override fun generate() = "Basic Report"
}

class PDFExporter : ReportExporter {
    override fun export(content: String) = "PDF: $content"
}

class ExcelExporter : ReportExporter {
    override fun export(content: String) = "Excel: $content"
}

class Report(
    private val generator: ReportGenerator,
    private val exporter: ReportExporter
) {
    fun createReport(): String {
        val content = generator.generate()
        return exporter.export(content)
    }
}

fun main() {
    val pdfReport = Report(BasicReportGenerator(), PDFExporter())
    println(pdfReport.createReport())
    
    val excelReport = Report(BasicReportGenerator(), ExcelExporter())
    println(excelReport.createReport())
}

// Преимущество: Можем добавлять новые экспортеры
// БЕЗ изменения существующего кода
```

### Таблица Сравнения

| Критерий | Наследование | Композиция |
|----------|-------------|------------|
| **Отношение** | IS-A (является) | HAS-A (имеет) |
| **Связанность** | Жесткая (tight coupling) | Слабая (loose coupling) |
| **Гибкость** | Фиксировано на этапе компиляции | Можно менять в runtime |
| **Множественное поведение** | Нет (только один родитель) | Да (много компонентов) |
| **Тестируемость** | Сложно (нужно тестировать всю иерархию) | Легко (мокируем зависимости) |
| **Инкапсуляция** | Нарушается (protected) | Сохраняется (private) |
| **Повторное использование** | Наследуем ВСЁ (даже ненужное) | Используем только нужное |
| **Изменение поведения** | Переопределение методов | Замена компонента |

---

## Dependency Injection и Композиция

### Почему Engine Должен Инджектиться Извне?

**Вы сказали:**
> "Экземпляр класса двигатель создается в классе машины и при этом не инджектируется извне"

**Это АНТИПАТТЕРН!** Вот почему:

#### ❌ Плохо: Создание Внутри

```kotlin
// ❌ АНТИПАТТЕРН: Жесткая зависимость
class Car {
    private val engine = PetrolEngine()  // Создаем внутри
    
    fun start() {
        engine.start()
    }
}

// Проблемы:
// 1. Нельзя заменить PetrolEngine на ElectricEngine
// 2. Нельзя протестировать Car без реального PetrolEngine
// 3. Car жестко привязан к PetrolEngine
// 4. Нарушается Dependency Inversion Principle

fun main() {
    val car = Car()  // Всегда PetrolEngine
    // Хотим ElectricEngine? Нужно создавать новый класс!
}
```

#### ✅ Хорошо: Dependency Injection

```kotlin
// ✅ ПРАВИЛЬНО: Инжектим зависимость
interface Engine {
    fun start()
    fun stop()
}

class PetrolEngine : Engine {
    override fun start() = println("Petrol engine started")
    override fun stop() = println("Petrol engine stopped")
}

class ElectricEngine : Engine {
    override fun start() = println("Electric engine started")
    override fun stop() = println("Electric engine stopped")
}

class HybridEngine : Engine {
    override fun start() = println("Hybrid engine started")
    override fun stop() = println("Hybrid engine stopped")
}

// Инжектим через конструктор
class Car(
    private val engine: Engine  // Dependency Injection
) {
    fun start() {
        println("Car starting...")
        engine.start()
        println("Car ready!")
    }
}

fun main() {
    // Можем создать любой тип машины!
    val petrolCar = Car(PetrolEngine())
    val electricCar = Car(ElectricEngine())
    val hybridCar = Car(HybridEngine())
    
    petrolCar.start()
    electricCar.start()
    hybridCar.start()
}

// Преимущества:
// 1. Гибкость - можем использовать любой Engine
// 2. Тестируемость - можем подставить mock
// 3. Слабая связанность - Car не знает о конкретной реализации
// 4. Соблюдается Dependency Inversion Principle
```

### Типы Dependency Injection

#### 1. Constructor Injection (Рекомендуется)

```kotlin
// ✅ ЛУЧШИЙ СПОСОБ: Через конструктор
class UserService(
    private val repository: UserRepository,
    private val logger: Logger
) {
    fun getUser(id: String): User? {
        logger.log("Fetching user $id")
        return repository.getUser(id)
    }
}

// Преимущества:
// 1. Зависимости явные и обязательные
// 2. Объект всегда в валидном состоянии
// 3. Immutable (val)
// 4. Легко тестировать
```

#### 2. Property Injection (Не рекомендуется)

```kotlin
// ⚠️ ДОПУСТИМО: Через свойства (для Android, например)
class MainActivity : AppCompatActivity() {
    lateinit var viewModel: MainViewModel  // Инжектится позже
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // viewModel инжектится DI фреймворком
    }
}

// Недостатки:
// 1. Объект может быть в невалидном состоянии
// 2. Нужен lateinit или nullable
// 3. Зависимости неявные
```

#### 3. Method Injection (Редко)

```kotlin
// ⚠️ РЕДКО: Через метод
class ReportGenerator {
    fun generate(exporter: ReportExporter): String {
        val content = "Report content"
        return exporter.export(content)
    }
}

// Используется когда зависимость нужна только для одного метода
```

### DI Frameworks в Android

```kotlin
// Hilt (рекомендуется для Android)
@HiltAndroidApp
class MyApplication : Application()

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides
    @Singleton
    fun provideEngine(): Engine = PetrolEngine()
    
    @Provides
    fun provideCar(engine: Engine): Car = Car(engine)
}

@AndroidEntryPoint
class MainActivity : AppCompatActivity() {
    @Inject
    lateinit var car: Car  // Hilt инжектит автоматически
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        car.start()
    }
}

// Преимущества DI фреймворков:
// 1. Автоматическое создание зависимостей
// 2. Управление жизненным циклом (Singleton, Factory)
// 3. Уменьшение boilerplate кода
```

---

## @Volatile - Что Это На Самом Деле

### ❌ Это НЕ Про Сериализацию!

**Вы сказали:**
> "Разве это не запрет на сериализацию?"

**Это НЕПРАВИЛЬНО!** Вы путаете с `@Transient`.

### Правильное Объяснение

#### @Volatile - Видимость в Многопоточности

```kotlin
// @Volatile - для многопоточного доступа
class Singleton private constructor() {
    companion object {
        @Volatile  // ← Для многопоточности!
        private var instance: Singleton? = null
        
        fun getInstance(): Singleton {
            return instance ?: synchronized(this) {
                instance ?: Singleton().also { instance = it }
            }
        }
    }
}

// Что делает @Volatile:
// 1. Гарантирует видимость изменений между потоками
// 2. Запрещает кеширование в регистрах CPU
// 3. Запрещает reordering операций компилятором
```

#### Проблема Без @Volatile

```kotlin
// ❌ БЕЗ @Volatile - может быть race condition
class Counter {
    private var count = 0  // НЕ volatile
    
    fun increment() {
        count++  // НЕ атомарная операция!
        // 1. Читаем count
        // 2. Увеличиваем на 1
        // 3. Записываем обратно
    }
}

fun main() {
    val counter = Counter()
    
    // Запускаем 1000 потоков
    val threads = List(1000) {
        Thread { counter.increment() }
    }
    
    threads.forEach { it.start() }
    threads.forEach { it.join() }
    
    println(counter.count)  // Ожидаем 1000, получаем меньше!
    // Потому что count++ НЕ атомарная операция
}
```

#### ✅ С @Volatile - Видимость Гарантирована

```kotlin
// ✅ С @Volatile - видимость гарантирована
class Flag {
    @Volatile
    var isRunning = true  // Изменения видны всем потокам
    
    fun stop() {
        isRunning = false  // Сразу видно другим потокам
    }
}

fun main() {
    val flag = Flag()
    
    // Поток 1: Читает флаг
    Thread {
        while (flag.isRunning) {
            // Работаем
        }
        println("Stopped!")
    }.start()
    
    // Поток 2: Меняет флаг
    Thread {
        Thread.sleep(1000)
        flag.stop()  // Изменение сразу видно потоку 1
    }.start()
}

// Без @Volatile поток 1 мог бы закешировать isRunning
// и не увидеть изменение!
```

### @Volatile vs @Transient

```kotlin
import java.io.Serializable

data class User(
    val name: String,
    
    @Volatile  // ← Для многопоточности
    var isOnline: Boolean,
    
    @Transient  // ← Для сериализации (НЕ сохраняется)
    var password: String = ""
) : Serializable

// @Volatile:
// - Гарантирует видимость между потоками
// - НЕ влияет на сериализацию
// - Используется для многопоточного доступа

// @Transient:
// - Исключает поле из сериализации
// - НЕ влияет на многопоточность
// - Используется для временных/секретных данных
```

### Когда Использовать @Volatile

```kotlin
// ✅ ПРАВИЛЬНО: Флаги состояния
class Worker {
    @Volatile
    var isCancelled = false
    
    fun cancel() {
        isCancelled = true
    }
    
    fun doWork() {
        while (!isCancelled) {
            // Работаем
        }
    }
}

// ✅ ПРАВИЛЬНО: Double-Checked Locking
class Singleton {
    companion object {
        @Volatile
        private var instance: Singleton? = null
        
        fun getInstance() = instance ?: synchronized(this) {
            instance ?: Singleton().also { instance = it }
        }
    }
}

// ❌ НЕПРАВИЛЬНО: Счетчики (нужен AtomicInteger)
class Counter {
    @Volatile
    var count = 0  // ❌ Видимость есть, но count++ НЕ атомарна!
    
    fun increment() {
        count++  // ❌ Race condition!
    }
}

// ✅ ПРАВИЛЬНО: Атомарные операции
import java.util.concurrent.atomic.AtomicInteger

class CounterFixed {
    private val count = AtomicInteger(0)
    
    fun increment() {
        count.incrementAndGet()  // ✅ Атомарно!
    }
    
    fun get() = count.get()
}
```

### Memory Visibility в Kotlin

```kotlin
// Проблема видимости памяти
class DataHolder {
    private var data: String? = null  // НЕ volatile
    private var ready = false         // НЕ volatile
    
    fun writer() {
        data = "Important data"  // 1
        ready = true             // 2
        // Компилятор может переставить местами!
    }
    
    fun reader(): String? {
        if (ready) {              // 3
            return data           // 4
            // Может вернуть null, даже если ready = true!
        }
        return null
    }
}

// ✅ Решение 1: @Volatile
class DataHolderFixed1 {
    private var data: String? = null
    @Volatile
    private var ready = false  // Запрещает reordering
    
    fun writer() {
        data = "Important data"
        ready = true  // Все предыдущие записи видны
    }
    
    fun reader(): String? {
        if (ready) {  // Все последующие чтения видят актуальные данные
            return data
        }
        return null
    }
}

// ✅ Решение 2: synchronized
class DataHolderFixed2 {
    private var data: String? = null
    private var ready = false
    private val lock = Any()
    
    fun writer() {
        synchronized(lock) {
            data = "Important data"
            ready = true
        }
    }
    
    fun reader(): String? {
        synchronized(lock) {
            if (ready) {
                return data
            }
            return null
        }
    }
}

// ✅ Решение 3: Корутины (рекомендуется в Kotlin)
class DataHolderFixed3 {
    private var data: String? = null
    private val mutex = Mutex()
    
    suspend fun writer() {
        mutex.withLock {
            data = "Important data"
        }
    }
    
    suspend fun reader(): String? {
        return mutex.withLock {
            data
        }
    }
}
```

---

## Практические Примеры

### Пример 1: Рефакторинг с Наследования на Композицию

```kotlin
// ❌ БЫЛО: Наследование
open class Employee(
    val name: String,
    val salary: Double
) {
    open fun calculateBonus(): Double = salary * 0.1
}

class Manager(name: String, salary: Double) : Employee(name, salary) {
    override fun calculateBonus(): Double = salary * 0.2
}

class Developer(name: String, salary: Double) : Employee(name, salary) {
    override fun calculateBonus(): Double = salary * 0.15
}

// Проблемы:
// 1. Нельзя изменить способ расчета бонуса в runtime
// 2. Жесткая связь с Employee
// 3. Дублирование кода

// ✅ СТАЛО: Композиция
interface BonusCalculator {
    fun calculate(salary: Double): Double
}

class ManagerBonusCalculator : BonusCalculator {
    override fun calculate(salary: Double) = salary * 0.2
}

class DeveloperBonusCalculator : BonusCalculator {
    override fun calculate(salary: Double) = salary * 0.15
}

class StandardBonusCalculator : BonusCalculator {
    override fun calculate(salary: Double) = salary * 0.1
}

class Employee(
    val name: String,
    val salary: Double,
    private val bonusCalculator: BonusCalculator
) {
    fun calculateBonus() = bonusCalculator.calculate(salary)
}

fun main() {
    val manager = Employee("Alice", 100000.0, ManagerBonusCalculator())
    val developer = Employee("Bob", 80000.0, DeveloperBonusCalculator())
    
    println("Manager bonus: ${manager.calculateBonus()}")
    println("Developer bonus: ${developer.calculateBonus()}")
    
    // Можем изменить калькулятор в runtime!
    val promotedDeveloper = Employee("Bob", 80000.0, ManagerBonusCalculator())
    println("Promoted developer bonus: ${promotedDeveloper.calculateBonus()}")
}
```

### Пример 2: Strategy Pattern (Композиция)

```kotlin
// Стратегия сортировки
interface SortStrategy {
    fun <T : Comparable<T>> sort(list: List<T>): List<T>
}

class QuickSort : SortStrategy {
    override fun <T : Comparable<T>> sort(list: List<T>): List<T> {
        println("Using QuickSort")
        return list.sorted()  // Упрощенно
    }
}

class MergeSort : SortStrategy {
    override fun <T : Comparable<T>> sort(list: List<T>): List<T> {
        println("Using MergeSort")
        return list.sorted()  // Упрощенно
    }
}

class BubbleSort : SortStrategy {
    override fun <T : Comparable<T>> sort(list: List<T>): List<T> {
        println("Using BubbleSort")
        return list.sorted()  // Упрощенно
    }
}

class Sorter<T : Comparable<T>>(
    private var strategy: SortStrategy
) {
    fun setStrategy(strategy: SortStrategy) {
        this.strategy = strategy
    }
    
    fun sort(list: List<T>): List<T> {
        return strategy.sort(list)
    }
}

fun main() {
    val numbers = listOf(5, 2, 8, 1, 9)
    val sorter = Sorter<Int>(QuickSort())
    
    println(sorter.sort(numbers))
    
    // Меняем стратегию в runtime
    sorter.setStrategy(MergeSort())
    println(sorter.sort(numbers))
    
    // Выбираем стратегию в зависимости от размера
    val largeList = (1..1000).shuffled()
    sorter.setStrategy(
        if (largeList.size > 100) QuickSort() else BubbleSort()
    )
    sorter.sort(largeList)
}
```

### Пример 3: Decorator Pattern (Композиция)

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

// Декораторы через композицию
class MilkDecorator(
    private val coffee: Coffee
) : Coffee {
    override fun cost() = coffee.cost() + 1.5
    override fun description() = "${coffee.description()} + milk"
}

class SugarDecorator(
    private val coffee: Coffee
) : Coffee {
    override fun cost() = coffee.cost() + 0.5
    override fun description() = "${coffee.description()} + sugar"
}

class WhippedCreamDecorator(
    private val coffee: Coffee
) : Coffee {
    override fun cost() = coffee.cost() + 2.0
    override fun description() = "${coffee.description()} + whipped cream"
}

fun main() {
    // Простой кофе
    var coffee: Coffee = SimpleCoffee()
    println("${coffee.description()}: $${coffee.cost()}")
    
    // Добавляем молоко
    coffee = MilkDecorator(coffee)
    println("${coffee.description()}: $${coffee.cost()}")
    
    // Добавляем сахар
    coffee = SugarDecorator(coffee)
    println("${coffee.description()}: $${coffee.cost()}")
    
    // Добавляем взбитые сливки
    coffee = WhippedCreamDecorator(coffee)
    println("${coffee.description()}: $${coffee.cost()}")
    
    // Вывод:
    // Simple coffee: $5.0
    // Simple coffee + milk: $6.5
    // Simple coffee + milk + sugar: $7.0
    // Simple coffee + milk + sugar + whipped cream: $9.0
}
```

---

## Итоговая Шпаргалка для Интервью

### Вопрос: Чем наследование плохо?

**Ответ:**
1. **Жесткая связанность** - наследник привязан к родителю
2. **Fragile Base Class** - изменение родителя ломает наследников
3. **Нарушение LSP** - наследник может не заменять родителя
4. **Нет гибкости в runtime** - поведение фиксировано
5. **Нет множественного наследования** - только один родитель
6. **Нарушение инкапсуляции** - protected открывает внутренности
7. **Глубокие иерархии** - сложно понимать и поддерживать

### Вопрос: Что использовать вместо наследования?

**Ответ:**
1. **Композиция** - "has-a" вместо "is-a"
2. **Интерфейсы** - контракты без реализации
3. **Делегирование** - передача работы другим объектам
4. **Паттерны** - Strategy, Decorator, etc.

### Вопрос: Чем композиция отличается от наследования?

**Ответ:**

| Наследование | Композиция |
|--------------|------------|
| IS-A (является) | HAS-A (имеет) |
| Жесткая связь | Слабая связь |
| Compile-time | Runtime |
| Один родитель | Много компонентов |
| Переопределение | Делегирование |
| Изменяем класс | Расширяем класс |

### Вопрос: Зачем инжектить зависимости?

**Ответ:**
1. **Гибкость** - можем менять реализацию
2. **Тестируемость** - можем подставлять моки
3. **Слабая связанность** - класс не знает о конкретной реализации
4. **SOLID** - соблюдаем Dependency Inversion Principle

### Вопрос: Что делает @Volatile?

**Ответ:**
1. **Видимость** - изменения видны всем потокам
2. **Запрет кеширования** - нельзя кешировать в регистрах
3. **Запрет reordering** - компилятор не переставляет операции
4. **НЕ про сериализацию** - это @Transient!
5. **НЕ атомарность** - для счетчиков нужен AtomicInteger

---

## Дополнительные Материалы

### Книги
- "Effective Java" by Joshua Bloch - глава про композицию
- "Design Patterns" by Gang of Four - паттерны на основе композиции
- "Clean Code" by Robert Martin - принципы проектирования

### Принципы
- **Favor composition over inheritance** - предпочитайте композицию
- **Program to an interface, not an implementation** - программируйте на интерфейсы
- **Dependency Inversion Principle** - зависьте от абстракций
- **Open/Closed Principle** - открыт для расширения, закрыт для изменения

### Паттерны на Основе Композиции
- **Strategy** - инкапсуляция алгоритмов
- **Decorator** - динамическое добавление функциональности
- **Composite** - древовидные структуры
- **Bridge** - разделение абстракции и реализации
- **Adapter** - адаптация интерфейсов
