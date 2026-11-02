# Фабрики в Kotlin: Simple Factory, Factory Method, Abstract Factory

## 0. Важная поправка
В GoF **нет** паттерна «Фабрика» как такового. В книге два порождающих паттерна:
- **Factory Method** (Фабричный метод)
- **Abstract Factory** (Абстрактная фабрика)

**Simple Factory** (простая фабрика) — не паттерн GoF, а идиома. Они не «производные от одного», это три разных вещи. На собеседовании это стоит сказать явно.

---

## 1. Кратко: в чём разница

| | Simple Factory | Factory Method | Abstract Factory |
|---|---|---|---|
| В GoF | Нет | Да | Да |
| Что создаёт | Один тип продукта | Один тип продукта | **Семейство** связанных продуктов |
| Механизм | Один метод с `when` | **Наследование**: подкласс переопределяет метод | **Композиция**: передаётся объект-фабрика |
| Расширение | Правка `when` (нарушает OCP) | Новый подкласс | Новая реализация фабрики |
| Суть | «Дай мне X по параметру» | «Подкласс решает, какой X создать» | «Дай набор согласованных X, Y, Z» |

Короткая фраза для интервью:
> Factory Method — один продукт, решение через наследование. Abstract Factory — семейство продуктов, решение через композицию (объект-фабрика). Simple Factory — просто статический метод с `when`.

---

## 2. Общий пример: уведомления / диалоги

```kotlin
interface Button {
    fun render(): String
}
```

---

## 3. Simple Factory (не GoF)

Один метод выбирает реализацию по параметру.

```kotlin
class AndroidButton : Button { override fun render() = "Android button" }
class IosButton : Button { override fun render() = "iOS button" }

enum class Platform { ANDROID, IOS }

object ButtonFactory {
    fun create(platform: Platform): Button = when (platform) {
        Platform.ANDROID -> AndroidButton()
        Platform.IOS -> IosButton()
    }
}

val button = ButtonFactory.create(Platform.ANDROID)
```

**Плюсы:** просто, скрывает конструкторы.
**Минусы:** новый тип = правка `when` (нарушение Open/Closed). С `sealed`/`enum` компилятор хотя бы требует exhaustive `when`.

**Kotlin-идиома:** `companion object` с `operator fun invoke` или `fun of(...)`:

```kotlin
interface Shape {
    companion object {
        operator fun invoke(type: String): Shape = when (type) {
            "circle" -> Circle()
            else -> Square()
        }
    }
}
class Circle : Shape
class Square : Shape

val s = Shape("circle")
```

---

## 4. Factory Method (GoF)

Базовый класс определяет **абстрактный метод создания**; подклассы решают, какой объект вернуть. Базовый класс при этом использует продукт в своей логике (Template Method + Factory Method).

```kotlin
interface Notification {
    fun send(text: String)
}

class PushNotification : Notification {
    override fun send(text: String) = println("Push: $text")
}
class EmailNotification : Notification {
    override fun send(text: String) = println("Email: $text")
}

// Creator
abstract class NotificationService {
    // Фабричный метод
    protected abstract fun createNotification(): Notification

    // Бизнес-логика, не знающая конкретного типа
    fun notifyUser(text: String) {
        val n = createNotification()
        n.send(text.trim())
    }
}

class PushService : NotificationService() {
    override fun createNotification() = PushNotification()
}
class EmailService : NotificationService() {
    override fun createNotification() = EmailNotification()
}

PushService().notifyUser("Привет")
EmailService().notifyUser("Привет")
```

**Ключевое:** выбор типа продукта делегирован **подклассу**. Клиент работает с `NotificationService`.

**Android-примеры:**
- `Fragment.onCreateView()`, `Activity.onCreate()` — шаблонные/фабричные методы
- `RecyclerView.Adapter.onCreateViewHolder()` — классический Factory Method: адаптер сам решает, какой `ViewHolder` создать
- `ViewModelProvider.Factory.create()` (ближе к Simple/Abstract, но часто приводят)
- `Calendar.getInstance()`, `NumberFormat.getInstance()` — статические фабричные методы (это не GoF Factory Method, а Simple Factory)

---

## 5. Abstract Factory (GoF)

Интерфейс для создания **семейства согласованных объектов**, без указания конкретных классов. Гарантирует, что продукты из одного семейства используются вместе.

```kotlin
interface Button { fun render(): String }
interface Checkbox { fun render(): String }

class MaterialButton : Button { override fun render() = "Material button" }
class MaterialCheckbox : Checkbox { override fun render() = "Material checkbox" }
class CupertinoButton : Button { override fun render() = "Cupertino button" }
class CupertinoCheckbox : Checkbox { override fun render() = "Cupertino checkbox" }

// Abstract Factory
interface UiFactory {
    fun createButton(): Button
    fun createCheckbox(): Checkbox
}

class MaterialUiFactory : UiFactory {
    override fun createButton() = MaterialButton()
    override fun createCheckbox() = MaterialCheckbox()
}
class CupertinoUiFactory : UiFactory {
    override fun createButton() = CupertinoButton()
    override fun createCheckbox() = CupertinoCheckbox()
}

// Клиент не знает о конкретных классах, фабрика внедряется
class SettingsScreen(private val factory: UiFactory) {
    fun draw() {
        println(factory.createButton().render())
        println(factory.createCheckbox().render())
    }
}

SettingsScreen(MaterialUiFactory()).draw()
SettingsScreen(CupertinoUiFactory()).draw()
```

**Ключевое:** фабрика — **объект**, передаётся как зависимость (DI). Невозможно случайно смешать `MaterialButton` и `CupertinoCheckbox`.

**Минус:** добавить новый тип продукта (например, `Switch`) = менять интерфейс и все фабрики.

**Реальные примеры:**
- KMP: `expect/actual` и платформенные фабрики для `HttpClientEngine`, драйверов БД
- Dagger/Hilt-модули, поставляющие семейства зависимостей по build variant (prod/mock)
- `DocumentBuilderFactory`, `LayoutInflater.Factory` (условно)

---

## 6. Как показать разницу на одном примере

Задача: «создавать кнопку под платформу».

- **Simple Factory:** `ButtonFactory.create(platform)` → `when`.
- **Factory Method:** `abstract class Dialog { abstract fun createButton(): Button }`, подклассы `AndroidDialog`, `IosDialog`. Кнопка одна, выбирает наследник.
- **Abstract Factory:** `UiFactory { createButton(); createCheckbox() }`. Нужны **несколько** связанных виджетов одной платформы.

Признак выбора:
1. Один продукт, нужен выбор по параметру → Simple Factory.
2. Один продукт, класс-родитель использует его и подклассы настраивают → Factory Method.
3. Несколько связанных продуктов, должны быть из одного семейства → Abstract Factory.

---

## 7. Kotlin-специфика

- **Лямбда как фабрика:** вместо интерфейса часто хватает `() -> T`.
  ```kotlin
  class Screen(private val buttonFactory: () -> Button)
  Screen(::MaterialButton)
  ```
- **`sealed interface` + `when`** даёт exhaustive Simple Factory без `else`.
- **`companion object`** — место для статических фабричных методов (`fromJson`, `of`, `create`). Приватный конструктор + фабричный метод позволяют валидацию и кэш.
- **`inline fun <reified T>`** позволяет фабрики по типу: `inline fun <reified T : Any> create(): T`.
- **Koin/Hilt `factory {}`** — это про scope (новый экземпляр на каждый запрос), а не про паттерн GoF. Частая путаница.

---

## 8. Вопросы для собеседования

**Чем Factory Method отличается от Abstract Factory?**
Factory Method — один метод, один продукт, наследование. Abstract Factory — объект с несколькими методами создания, семейство продуктов, композиция. Abstract Factory часто реализуется набором фабричных методов.

**Почему Simple Factory — не паттерн GoF?**
В книге его нет; это идиома: статический метод с условной логикой, без полиморфизма создателя.

**Нарушает ли Simple Factory SOLID?**
Open/Closed: добавление типа требует правки `when`. Решается Factory Method, Abstract Factory или регистрацией создателей в `Map<Key, () -> T>`.

**Когда не стоит использовать?**
Когда конструктор достаточно прост, а вариантов нет. В Kotlin часто хватает именованных аргументов, значений по умолчанию и лямбд.

**Где в Android Factory Method?**
`RecyclerView.Adapter.onCreateViewHolder`, `Fragment.onCreateView`, `Activity.onCreateOptionsMenu`.

**Связь с DI?**
DI-контейнер заменяет ручные фабрики; Abstract Factory хорошо инжектится как зависимость.

---

## 9. Шпаргалка

- **Simple Factory** — `when` в одном месте. Не GoF.
- **Factory Method** — наследование, подкласс создаёт продукт.
- **Abstract Factory** — композиция, фабрика создаёт семейство продуктов.
- Все три скрывают конкретные классы от клиента и снижают связанность.
