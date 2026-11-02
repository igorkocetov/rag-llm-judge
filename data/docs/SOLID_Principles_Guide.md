# SOLID Principles - Kotlin Interview Guide

## Содержание
1. [Single Responsibility Principle (SRP)](#single-responsibility-principle)
2. [Open/Closed Principle (OCP)](#openclosed-principle)
3. [Liskov Substitution Principle (LSP)](#liskov-substitution-principle)
4. [Interface Segregation Principle (ISP)](#interface-segregation-principle)
5. [Dependency Inversion Principle (DIP)](#dependency-inversion-principle)

---

## Single Responsibility Principle (SRP)

### Определение
**Класс должен иметь только одну причину для изменения**, то есть только одну ответственность.

### ❌ Нарушение принципа

```kotlin
class User(
    val name: String,
    val email: String
) {
    fun saveToDatabase() {
        val connection = DatabaseConnection.connect()
        connection.execute("INSERT INTO users VALUES ('$name', '$email')")
    }
    
    fun sendWelcomeEmail() {
        val emailService = EmailService()
        emailService.send(email, "Welcome!", "Hello $name")
    }
    
    fun validateEmail(): Boolean {
        return email.contains("@") && email.contains(".")
    }
    
    fun generateReport(): String {
        return "User Report: $name ($email)"
    }
}
```

**Проблемы:**
- Класс отвечает за: хранение данных, работу с БД, отправку email, валидацию, генерацию отчетов
- Изменение логики БД требует изменения класса User
- Изменение формата email требует изменения класса User
- Сложно тестировать

### ✅ Правильная реализация

```kotlin
data class User(
    val name: String,
    val email: String
)

class UserRepository {
    fun save(user: User) {
        val connection = DatabaseConnection.connect()
        connection.execute("INSERT INTO users VALUES ('${user.name}', '${user.email}')")
    }
}

class EmailValidator {
    fun validate(email: String): Boolean {
        return email.contains("@") && email.contains(".")
    }
}

class WelcomeEmailService {
    fun sendWelcome(user: User) {
        val emailService = EmailService()
        emailService.send(user.email, "Welcome!", "Hello ${user.name}")
    }
}

class UserReportGenerator {
    fun generate(user: User): String {
        return "User Report: ${user.name} (${user.email})"
    }
}
```

**Преимущества:**
- Каждый класс имеет одну ответственность
- Легко тестировать каждый компонент отдельно
- Изменения в одной области не влияют на другие

---

## Open/Closed Principle (OCP)

### Определение
**Классы должны быть открыты для расширения, но закрыты для модификации.** Можно добавлять новую функциональность без изменения существующего кода.

### ❌ Нарушение принципа

```kotlin
class PaymentProcessor {
    fun processPayment(amount: Double, type: String) {
        when (type) {
            "CREDIT_CARD" -> {
                println("Processing credit card payment: $amount")
                // логика обработки кредитной карты
            }
            "PAYPAL" -> {
                println("Processing PayPal payment: $amount")
                // логика обработки PayPal
            }
            "BITCOIN" -> {
                println("Processing Bitcoin payment: $amount")
                // логика обработки Bitcoin
            }
            else -> throw IllegalArgumentException("Unknown payment type")
        }
    }
}
```

**Проблемы:**
- Для добавления нового способа оплаты нужно модифицировать класс
- Нарушается принцип закрытости для модификации
- Растет сложность метода с каждым новым типом

### ✅ Правильная реализация

```kotlin
interface PaymentMethod {
    fun process(amount: Double)
}

class CreditCardPayment : PaymentMethod {
    override fun process(amount: Double) {
        println("Processing credit card payment: $amount")
        // логика обработки кредитной карты
    }
}

class PayPalPayment : PaymentMethod {
    override fun process(amount: Double) {
        println("Processing PayPal payment: $amount")
        // логика обработки PayPal
    }
}

class BitcoinPayment : PaymentMethod {
    override fun process(amount: Double) {
        println("Processing Bitcoin payment: $amount")
        // логика обработки Bitcoin
    }
}

class PaymentProcessor {
    fun processPayment(amount: Double, paymentMethod: PaymentMethod) {
        paymentMethod.process(amount)
    }
}

// Использование
fun main() {
    val processor = PaymentProcessor()
    processor.processPayment(100.0, CreditCardPayment())
    processor.processPayment(200.0, PayPalPayment())
    
    // Добавление нового метода оплаты не требует изменения PaymentProcessor
    processor.processPayment(300.0, BitcoinPayment())
}
```

**Преимущества:**
- Новые способы оплаты добавляются без изменения существующего кода
- PaymentProcessor закрыт для модификации
- Легко расширять функциональность

---

## Liskov Substitution Principle (LSP)

### Определение
**Объекты подклассов должны быть взаимозаменяемы с объектами базового класса без нарушения корректности программы.** Наследники не должны нарушать контракт родительского класса.

### Важные аспекты LSP:
1. **Предусловия не могут быть усилены** в подклассе
2. **Постусловия не могут быть ослаблены** в подклассе
3. **Инварианты должны сохраняться**
4. **Поведение должно быть согласованным**

### ❌ Нарушение принципа - Пример 1 (Классический с птицами)

```kotlin
open class Bird {
    open fun fly() {
        println("Flying in the sky")
    }
}

class Sparrow : Bird() {
    override fun fly() {
        println("Sparrow flying")
    }
}

class Penguin : Bird() {
    override fun fly() {
        throw UnsupportedOperationException("Penguins can't fly!")
    }
}

fun makeBirdFly(bird: Bird) {
    bird.fly() // Упадет с exception для Penguin!
}
```

**Проблема:** Penguin нарушает контракт Bird - метод fly() должен работать для всех птиц.

### ❌ Нарушение принципа - Пример 2 (Изменение правил валидации)

```kotlin
open class Rectangle {
    open var width: Int = 0
        set(value) {
            require(value > 0) { "Width must be positive" }
            field = value
        }
    
    open var height: Int = 0
        set(value) {
            require(value > 0) { "Height must be positive" }
            field = value
        }
    
    open fun area(): Int = width * height
}

class Square : Rectangle() {
    override var width: Int = 0
        set(value) {
            field = value
            super.height = value // Нарушение: меняем height при установке width
        }
    
    override var height: Int = 0
        set(value) {
            field = value
            super.width = value // Нарушение: меняем width при установке height
        }
}

fun testRectangle(rectangle: Rectangle) {
    rectangle.width = 5
    rectangle.height = 10
    println("Expected area: 50, Actual: ${rectangle.area()}")
    // Для Square получим 100 вместо 50!
}
```

**Проблема:** Square нарушает поведение Rectangle - изменение одной стороны не должно влиять на другую.

### ❌ Нарушение принципа - Пример 3 (Усиление предусловий)

```kotlin
open class Account {
    protected var balance: Double = 0.0
    
    open fun withdraw(amount: Double) {
        require(amount > 0) { "Amount must be positive" }
        require(balance >= amount) { "Insufficient funds" }
        balance -= amount
    }
}

class PremiumAccount : Account() {
    override fun withdraw(amount: Double) {
        // НАРУШЕНИЕ: усиливаем предусловие
        require(amount > 0) { "Amount must be positive" }
        require(amount <= 10000) { "Premium accounts can't withdraw more than 10000" }
        require(balance >= amount) { "Insufficient funds" }
        balance -= amount
    }
}

fun processWithdrawal(account: Account, amount: Double) {
    account.withdraw(amount) // Упадет для PremiumAccount при amount > 10000
}
```

**Проблема:** PremiumAccount добавляет дополнительное ограничение, которого не было в базовом классе.

### ❌ Нарушение принципа - Пример 4 (Ослабление постусловий)

```kotlin
open class DataValidator {
    open fun validate(data: String): Boolean {
        // Гарантирует: если вернул true, то data не пустая и содержит только буквы
        return data.isNotEmpty() && data.all { it.isLetter() }
    }
}

class LenientValidator : DataValidator() {
    override fun validate(data: String): Boolean {
        // НАРУШЕНИЕ: ослабляем постусловие - теперь true может быть и для цифр
        return data.isNotEmpty()
    }
}

fun processValidData(validator: DataValidator, data: String) {
    if (validator.validate(data)) {
        // Ожидаем, что data содержит только буквы
        val upperCase = data.uppercase() // Может упасть для цифр в некоторых случаях
        println("Processing: $upperCase")
    }
}
```

### ✅ Правильная реализация - Пример 1 (Птицы)

```kotlin
interface Bird {
    fun eat()
    fun makeSound()
}

interface FlyingBird : Bird {
    fun fly()
}

class Sparrow : FlyingBird {
    override fun eat() {
        println("Sparrow eating seeds")
    }
    
    override fun makeSound() {
        println("Chirp chirp")
    }
    
    override fun fly() {
        println("Sparrow flying")
    }
}

class Penguin : Bird {
    override fun eat() {
        println("Penguin eating fish")
    }
    
    override fun makeSound() {
        println("Penguin sound")
    }
    
    fun swim() {
        println("Penguin swimming")
    }
}

fun makeFlyingBirdFly(bird: FlyingBird) {
    bird.fly() // Работает только для летающих птиц
}
```

### ✅ Правильная реализация - Пример 2 (Прямоугольник)

```kotlin
interface Shape {
    fun area(): Int
}

class Rectangle(
    var width: Int,
    var height: Int
) : Shape {
    init {
        require(width > 0) { "Width must be positive" }
        require(height > 0) { "Height must be positive" }
    }
    
    override fun area(): Int = width * height
}

class Square(
    var side: Int
) : Shape {
    init {
        require(side > 0) { "Side must be positive" }
    }
    
    override fun area(): Int = side * side
}

fun calculateArea(shape: Shape): Int {
    return shape.area() // Работает корректно для обоих
}
```

### ✅ Правильная реализация - Пример 3 (Аккаунты)

```kotlin
interface WithdrawableAccount {
    fun withdraw(amount: Double)
    fun getMaxWithdrawalAmount(): Double
}

class StandardAccount : WithdrawableAccount {
    private var balance: Double = 0.0
    
    override fun withdraw(amount: Double) {
        require(amount > 0) { "Amount must be positive" }
        require(amount <= getMaxWithdrawalAmount()) { "Exceeds maximum withdrawal" }
        require(balance >= amount) { "Insufficient funds" }
        balance -= amount
    }
    
    override fun getMaxWithdrawalAmount(): Double = Double.MAX_VALUE
}

class PremiumAccount : WithdrawableAccount {
    private var balance: Double = 0.0
    
    override fun withdraw(amount: Double) {
        require(amount > 0) { "Amount must be positive" }
        require(amount <= getMaxWithdrawalAmount()) { "Exceeds maximum withdrawal" }
        require(balance >= amount) { "Insufficient funds" }
        balance -= amount
    }
    
    override fun getMaxWithdrawalAmount(): Double = 10000.0
}

fun processWithdrawal(account: WithdrawableAccount, amount: Double) {
    val maxAmount = account.getMaxWithdrawalAmount()
    if (amount <= maxAmount) {
        account.withdraw(amount) // Работает корректно
    } else {
        println("Amount exceeds maximum: $maxAmount")
    }
}
```

### ✅ Правильная реализация - Пример 4 (Валидаторы)

```kotlin
interface Validator {
    fun validate(data: String): ValidationResult
}

data class ValidationResult(
    val isValid: Boolean,
    val rules: Set<ValidationRule>
)

enum class ValidationRule {
    NOT_EMPTY,
    ONLY_LETTERS,
    MIN_LENGTH
}

class StrictValidator : Validator {
    override fun validate(data: String): ValidationResult {
        val isValid = data.isNotEmpty() && data.all { it.isLetter() }
        return ValidationResult(
            isValid = isValid,
            rules = setOf(ValidationRule.NOT_EMPTY, ValidationRule.ONLY_LETTERS)
        )
    }
}

class LenientValidator : Validator {
    override fun validate(data: String): ValidationResult {
        val isValid = data.isNotEmpty()
        return ValidationResult(
            isValid = isValid,
            rules = setOf(ValidationRule.NOT_EMPTY)
        )
    }
}

fun processData(validator: Validator, data: String) {
    val result = validator.validate(data)
    if (result.isValid) {
        if (ValidationRule.ONLY_LETTERS in result.rules) {
            println("Processing letters only: ${data.uppercase()}")
        } else {
            println("Processing any data: $data")
        }
    }
}
```

---

## Interface Segregation Principle (ISP)

### Определение
**Клиенты не должны зависеть от интерфейсов, которые они не используют.** Лучше иметь много специализированных интерфейсов, чем один универсальный.

### ❌ Нарушение принципа

```kotlin
interface Worker {
    fun work()
    fun eat()
    fun sleep()
    fun getSalary()
    fun attendMeeting()
    fun writeCode()
    fun designUI()
}

class Developer : Worker {
    override fun work() { println("Writing code") }
    override fun eat() { println("Eating") }
    override fun sleep() { println("Sleeping") }
    override fun getSalary() { println("Getting salary") }
    override fun attendMeeting() { println("Attending meeting") }
    override fun writeCode() { println("Coding") }
    override fun designUI() {
        throw UnsupportedOperationException("Developer doesn't design UI")
    }
}

class Designer : Worker {
    override fun work() { println("Designing") }
    override fun eat() { println("Eating") }
    override fun sleep() { println("Sleeping") }
    override fun getSalary() { println("Getting salary") }
    override fun attendMeeting() { println("Attending meeting") }
    override fun writeCode() {
        throw UnsupportedOperationException("Designer doesn't write code")
    }
    override fun designUI() { println("Designing UI") }
}

class Robot : Worker {
    override fun work() { println("Working") }
    override fun eat() {
        throw UnsupportedOperationException("Robot doesn't eat")
    }
    override fun sleep() {
        throw UnsupportedOperationException("Robot doesn't sleep")
    }
    override fun getSalary() {
        throw UnsupportedOperationException("Robot doesn't get salary")
    }
    override fun attendMeeting() { println("Attending meeting") }
    override fun writeCode() { println("Executing code") }
    override fun designUI() {
        throw UnsupportedOperationException("Robot doesn't design")
    }
}
```

**Проблемы:**
- Классы вынуждены реализовывать методы, которые им не нужны
- Много UnsupportedOperationException
- Интерфейс слишком "толстый"

### ✅ Правильная реализация

```kotlin
interface Workable {
    fun work()
}

interface Eatable {
    fun eat()
}

interface Sleepable {
    fun sleep()
}

interface Payable {
    fun getSalary()
}

interface MeetingAttendee {
    fun attendMeeting()
}

interface Programmer {
    fun writeCode()
}

interface UIDesigner {
    fun designUI()
}

class Developer : Workable, Eatable, Sleepable, Payable, MeetingAttendee, Programmer {
    override fun work() { println("Writing code") }
    override fun eat() { println("Eating") }
    override fun sleep() { println("Sleeping") }
    override fun getSalary() { println("Getting salary") }
    override fun attendMeeting() { println("Attending meeting") }
    override fun writeCode() { println("Coding") }
}

class Designer : Workable, Eatable, Sleepable, Payable, MeetingAttendee, UIDesigner {
    override fun work() { println("Designing") }
    override fun eat() { println("Eating") }
    override fun sleep() { println("Sleeping") }
    override fun getSalary() { println("Getting salary") }
    override fun attendMeeting() { println("Attending meeting") }
    override fun designUI() { println("Designing UI") }
}

class Robot : Workable, MeetingAttendee, Programmer {
    override fun work() { println("Working") }
    override fun attendMeeting() { println("Attending meeting") }
    override fun writeCode() { println("Executing code") }
}

fun conductMeeting(attendees: List<MeetingAttendee>) {
    attendees.forEach { it.attendMeeting() }
}

fun payEmployees(employees: List<Payable>) {
    employees.forEach { it.getSalary() }
}
```

**Преимущества:**
- Каждый класс реализует только нужные ему интерфейсы
- Нет пустых или бросающих исключения методов
- Гибкость в композиции поведения

---

## Dependency Inversion Principle (DIP)

### Определение
**1. Модули верхнего уровня не должны зависеть от модулей нижнего уровня. Оба должны зависеть от абстракций.**
**2. Абстракции не должны зависеть от деталей. Детали должны зависеть от абстракций.**

### Аналогия с розеткой
Как вы правильно отметили - это принцип розетки и вилки:
- **Модуль верхнего уровня**: Пылесос, телевизор, зарядка телефона (бизнес-логика)
- **Модуль нижнего уровня**: Электропроводка в стене (инфраструктура)
- **Абстракция**: Розетка (интерфейс)

Без розетки пришлось бы перепаивать провода каждый раз при смене устройства. Розетка позволяет подключать любое устройство с подходящей вилкой.

### ❌ Нарушение принципа - Пример 1 (Прямая зависимость)

```kotlin
class MySQLDatabase {
    fun connect() {
        println("Connecting to MySQL")
    }
    
    fun saveUser(name: String, email: String) {
        println("Saving to MySQL: $name, $email")
    }
    
    fun getUser(id: Int): String {
        return "User from MySQL with id: $id"
    }
}

class UserService {
    // НАРУШЕНИЕ: зависимость от конкретной реализации
    private val database = MySQLDatabase()
    
    fun registerUser(name: String, email: String) {
        database.connect()
        database.saveUser(name, email)
        println("User registered")
    }
    
    fun getUser(id: Int): String {
        database.connect()
        return database.getUser(id)
    }
}
```

**Проблемы:**
- UserService жестко привязан к MySQL
- Невозможно переключиться на PostgreSQL или MongoDB без изменения UserService
- Сложно тестировать - нельзя подставить mock
- Нарушение принципа: верхний уровень (UserService) зависит от нижнего (MySQLDatabase)

### ❌ Нарушение принципа - Пример 2 (Множественные зависимости)

```kotlin
class EmailSender {
    fun sendEmail(to: String, subject: String, body: String) {
        println("Sending email to $to")
    }
}

class SMSSender {
    fun sendSMS(phone: String, message: String) {
        println("Sending SMS to $phone")
    }
}

class PushNotificationSender {
    fun sendPush(userId: String, message: String) {
        println("Sending push to $userId")
    }
}

class NotificationService {
    // НАРУШЕНИЕ: зависимость от конкретных реализаций
    private val emailSender = EmailSender()
    private val smsSender = SMSSender()
    private val pushSender = PushNotificationSender()
    
    fun notifyUser(userId: String, message: String, type: String) {
        when (type) {
            "EMAIL" -> emailSender.sendEmail("user@example.com", "Notification", message)
            "SMS" -> smsSender.sendSMS("+1234567890", message)
            "PUSH" -> pushSender.sendPush(userId, message)
        }
    }
}
```

**Проблемы:**
- NotificationService зависит от трех конкретных классов
- Добавление нового канала требует изменения NotificationService
- Невозможно легко заменить реализацию

### ❌ Нарушение принципа - Пример 3 (Android пример)

```kotlin
class NetworkManager {
    fun fetchData(url: String): String {
        println("Fetching from $url using OkHttp")
        return "Data from network"
    }
}

class CacheManager {
    fun saveToCache(key: String, data: String) {
        println("Saving to SharedPreferences")
    }
    
    fun getFromCache(key: String): String? {
        return "Cached data"
    }
}

class UserRepository {
    // НАРУШЕНИЕ: зависимость от конкретных реализаций
    private val network = NetworkManager()
    private val cache = CacheManager()
    
    fun getUser(userId: String): String {
        val cached = cache.getFromCache(userId)
        if (cached != null) return cached
        
        val data = network.fetchData("https://api.example.com/users/$userId")
        cache.saveToCache(userId, data)
        return data
    }
}
```

### ✅ Правильная реализация - Пример 1 (База данных)

```kotlin
// Абстракция (розетка)
interface Database {
    fun connect()
    fun saveUser(name: String, email: String)
    fun getUser(id: Int): String
}

// Модули нижнего уровня (провода в стене)
class MySQLDatabase : Database {
    override fun connect() {
        println("Connecting to MySQL")
    }
    
    override fun saveUser(name: String, email: String) {
        println("Saving to MySQL: $name, $email")
    }
    
    override fun getUser(id: Int): String {
        return "User from MySQL with id: $id"
    }
}

class PostgreSQLDatabase : Database {
    override fun connect() {
        println("Connecting to PostgreSQL")
    }
    
    override fun saveUser(name: String, email: String) {
        println("Saving to PostgreSQL: $name, $email")
    }
    
    override fun getUser(id: Int): String {
        return "User from PostgreSQL with id: $id"
    }
}

class MongoDatabase : Database {
    override fun connect() {
        println("Connecting to MongoDB")
    }
    
    override fun saveUser(name: String, email: String) {
        println("Saving to MongoDB: $name, $email")
    }
    
    override fun getUser(id: Int): String {
        return "User from MongoDB with id: $id"
    }
}

// Модуль верхнего уровня (пылесос/телевизор)
class UserService(
    private val database: Database // Зависимость от абстракции!
) {
    fun registerUser(name: String, email: String) {
        database.connect()
        database.saveUser(name, email)
        println("User registered")
    }
    
    fun getUser(id: Int): String {
        database.connect()
        return database.getUser(id)
    }
}

// Использование
fun main() {
    // Легко переключаемся между реализациями
    val mysqlService = UserService(MySQLDatabase())
    mysqlService.registerUser("John", "john@example.com")
    
    val postgresService = UserService(PostgreSQLDatabase())
    postgresService.registerUser("Jane", "jane@example.com")
    
    val mongoService = UserService(MongoDatabase())
    mongoService.registerUser("Bob", "bob@example.com")
}
```

### ✅ Правильная реализация - Пример 2 (Уведомления)

```kotlin
// Абстракция
interface NotificationChannel {
    fun send(recipient: String, message: String)
}

// Конкретные реализации
class EmailNotification : NotificationChannel {
    override fun send(recipient: String, message: String) {
        println("Sending email to $recipient: $message")
    }
}

class SMSNotification : NotificationChannel {
    override fun send(recipient: String, message: String) {
        println("Sending SMS to $recipient: $message")
    }
}

class PushNotification : NotificationChannel {
    override fun send(recipient: String, message: String) {
        println("Sending push to $recipient: $message")
    }
}

// Новый канал добавляется без изменения NotificationService
class TelegramNotification : NotificationChannel {
    override fun send(recipient: String, message: String) {
        println("Sending Telegram message to $recipient: $message")
    }
}

// Модуль верхнего уровня
class NotificationService(
    private val channels: List<NotificationChannel>
) {
    fun notifyUser(recipient: String, message: String) {
        channels.forEach { channel ->
            channel.send(recipient, message)
        }
    }
}

// Использование
fun main() {
    val service = NotificationService(
        listOf(
            EmailNotification(),
            SMSNotification(),
            PushNotification(),
            TelegramNotification() // Легко добавили новый канал
        )
    )
    
    service.notifyUser("user123", "Hello!")
}
```

### ✅ Правильная реализация - Пример 3 (Android Repository)

```kotlin
// Абстракции
interface NetworkDataSource {
    suspend fun fetchUser(userId: String): String
}

interface CacheDataSource {
    suspend fun saveUser(userId: String, data: String)
    suspend fun getUser(userId: String): String?
}

// Конкретные реализации (модули нижнего уровня)
class OkHttpNetworkDataSource : NetworkDataSource {
    override suspend fun fetchUser(userId: String): String {
        println("Fetching from network using OkHttp")
        return "User data from network"
    }
}

class RetrofitNetworkDataSource : NetworkDataSource {
    override suspend fun fetchUser(userId: String): String {
        println("Fetching from network using Retrofit")
        return "User data from Retrofit"
    }
}

class SharedPreferencesCacheDataSource : CacheDataSource {
    override suspend fun saveUser(userId: String, data: String) {
        println("Saving to SharedPreferences")
    }
    
    override suspend fun getUser(userId: String): String? {
        return "Cached user from SharedPreferences"
    }
}

class RoomCacheDataSource : CacheDataSource {
    override suspend fun saveUser(userId: String, data: String) {
        println("Saving to Room database")
    }
    
    override suspend fun getUser(userId: String): String? {
        return "Cached user from Room"
    }
}

// Модуль верхнего уровня
class UserRepository(
    private val networkDataSource: NetworkDataSource,
    private val cacheDataSource: CacheDataSource
) {
    suspend fun getUser(userId: String): String {
        val cached = cacheDataSource.getUser(userId)
        if (cached != null) return cached
        
        val data = networkDataSource.fetchUser(userId)
        cacheDataSource.saveUser(userId, data)
        return data
    }
}

// Использование с разными комбинациями
fun main() {
    // Комбинация 1: OkHttp + SharedPreferences
    val repo1 = UserRepository(
        OkHttpNetworkDataSource(),
        SharedPreferencesCacheDataSource()
    )
    
    // Комбинация 2: Retrofit + Room
    val repo2 = UserRepository(
        RetrofitNetworkDataSource(),
        RoomCacheDataSource()
    )
    
    // Легко меняем реализации без изменения UserRepository
}
```

### ✅ Правильная реализация - Пример 4 (Dependency Injection)

```kotlin
// Абстракции
interface Logger {
    fun log(message: String)
}

interface Analytics {
    fun trackEvent(event: String)
}

interface ConfigProvider {
    fun getApiUrl(): String
    fun getTimeout(): Long
}

// Конкретные реализации
class ConsoleLogger : Logger {
    override fun log(message: String) {
        println("[LOG] $message")
    }
}

class FileLogger : Logger {
    override fun log(message: String) {
        println("[FILE] Writing to file: $message")
    }
}

class FirebaseAnalytics : Analytics {
    override fun trackEvent(event: String) {
        println("[FIREBASE] Tracking: $event")
    }
}

class RemoteConfig : ConfigProvider {
    override fun getApiUrl(): String = "https://api.production.com"
    override fun getTimeout(): Long = 30000
}

class LocalConfig : ConfigProvider {
    override fun getApiUrl(): String = "http://localhost:8080"
    override fun getTimeout(): Long = 5000
}

// Модуль верхнего уровня
class ApiClient(
    private val logger: Logger,
    private val analytics: Analytics,
    private val config: ConfigProvider
) {
    fun makeRequest(endpoint: String) {
        val url = "${config.getApiUrl()}/$endpoint"
        logger.log("Making request to $url")
        analytics.trackEvent("api_request")
        
        println("Request with timeout: ${config.getTimeout()}ms")
    }
}

// Использование
fun main() {
    // Production конфигурация
    val prodClient = ApiClient(
        FileLogger(),
        FirebaseAnalytics(),
        RemoteConfig()
    )
    prodClient.makeRequest("users")
    
    // Development конфигурация
    val devClient = ApiClient(
        ConsoleLogger(),
        object : Analytics {
            override fun trackEvent(event: String) {
                println("[DEV] Skipping analytics")
            }
        },
        LocalConfig()
    )
    devClient.makeRequest("users")
}
```

### Преимущества DIP

1. **Гибкость**: Легко заменять реализации
2. **Тестируемость**: Можно подставлять mock-объекты
3. **Масштабируемость**: Добавление новых реализаций не требует изменения существующего кода
4. **Независимость**: Модули не знают о конкретных реализациях друг друга
5. **Переиспользование**: Один модуль верхнего уровня работает с разными реализациями

### DIP в Android с Hilt/Dagger

```kotlin
// Абстракции
interface UserRepository {
    suspend fun getUser(id: String): User
}

interface AuthService {
    suspend fun login(email: String, password: String): Token
}

// Конкретные реализации
class UserRepositoryImpl @Inject constructor(
    private val api: ApiService,
    private val database: UserDao
) : UserRepository {
    override suspend fun getUser(id: String): User {
        return database.getUser(id) ?: api.fetchUser(id).also {
            database.insertUser(it)
        }
    }
}

class AuthServiceImpl @Inject constructor(
    private val api: ApiService,
    private val tokenStorage: TokenStorage
) : AuthService {
    override suspend fun login(email: String, password: String): Token {
        val token = api.login(email, password)
        tokenStorage.saveToken(token)
        return token
    }
}

// ViewModel зависит от абстракций
class UserViewModel @Inject constructor(
    private val userRepository: UserRepository,
    private val authService: AuthService
) : ViewModel() {
    
    fun loadUser(id: String) {
        viewModelScope.launch {
            val user = userRepository.getUser(id)
            // обработка
        }
    }
    
    fun login(email: String, password: String) {
        viewModelScope.launch {
            val token = authService.login(email, password)
            // обработка
        }
    }
}

// Модуль Hilt
@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    
    @Binds
    abstract fun bindUserRepository(
        impl: UserRepositoryImpl
    ): UserRepository
    
    @Binds
    abstract fun bindAuthService(
        impl: AuthServiceImpl
    ): AuthService
}
```

---

## Итоговая таблица SOLID

| Принцип | Суть | Ключевой вопрос |
|---------|------|-----------------|
| **SRP** | Один класс = одна ответственность | Сколько причин для изменения класса? |
| **OCP** | Открыт для расширения, закрыт для модификации | Нужно ли менять код при добавлении функции? |
| **LSP** | Подклассы заменяют базовый класс без нарушений | Можно ли заменить родителя наследником? |
| **ISP** | Много маленьких интерфейсов лучше одного большого | Есть ли неиспользуемые методы? |
| **DIP** | Зависимость от абстракций, а не от реализаций | Зависит ли код от конкретных классов? |

## Вопросы для интервью

### SRP
- Как определить, что класс нарушает SRP?
- Может ли класс иметь несколько методов и соблюдать SRP?

### OCP
- Как добавить новую функциональность без изменения существующего кода?
- Какие паттерны помогают соблюдать OCP? (Strategy, Template Method, Decorator)

### LSP
- В чем разница между LSP и простым наследованием?
- Что такое контракт класса и как его не нарушить?
- Приведите пример, где наследование кажется логичным, но нарушает LSP

### ISP
- Когда стоит разделить интерфейс на несколько?
- Как ISP связан с SRP?

### DIP
- В чем разница между DIP и Dependency Injection?
- Как DIP помогает в тестировании?
- Объясните аналогию с розеткой и вилкой
- Что такое модули верхнего и нижнего уровня?

## Практические советы

1. **Не переусложняйте**: SOLID - это принципы, а не догмы. Иногда простое решение лучше "правильного"
2. **Рефакторинг**: Не обязательно писать идеальный код сразу. Рефакторьте по мере роста проекта
3. **Баланс**: Найдите баланс между гибкостью и простотой
4. **Тестирование**: Если код сложно тестировать - вероятно нарушены SOLID принципы
5. **Code Review**: Обсуждайте архитектурные решения с командой
