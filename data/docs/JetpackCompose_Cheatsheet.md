# Jetpack Compose - Шпаргалка для интервью

## Основные Layout контейнеры

### Column (LinearLayout vertical)
```kotlin
Column(
    verticalArrangement = Arrangement.Top,  // Top, Center, Bottom, SpaceBetween
    horizontalAlignment = Alignment.Start   // Start, CenterHorizontally, End
) {
    Text("Элемент 1")
    Text("Элемент 2")
}
```

### Row (LinearLayout horizontal)
```kotlin
Row(
    horizontalArrangement = Arrangement.SpaceBetween,
    verticalAlignment = Alignment.CenterVertically
) {
    Icon(Icons.Default.Home, null)
    Text("Главная")
}
```

### Box (FrameLayout)
```kotlin
Box(contentAlignment = Alignment.Center) {
    Image(...)  // Фон
    Text("Поверх изображения")  // Поверх
}
```

### LazyColumn (RecyclerView vertical)
```kotlin
LazyColumn {
    items(userList) { user ->
        UserItem(user)
    }
    itemsIndexed(list) { index, item -> }
    items(100) { index -> }
}
```

### LazyRow (RecyclerView horizontal)
```kotlin
LazyRow {
    items(imageList) { image -> Image(...) }
}
```

### LazyVerticalGrid (RecyclerView + GridLayoutManager)
```kotlin
LazyVerticalGrid(
    columns = GridCells.Fixed(2)  // или GridCells.Adaptive(100.dp)
) {
    items(photoList) { PhotoCard(it) }
}
```

### Scaffold ⭐ ВАЖНО!
**Контейнер верхнего уровня для Material Design экрана**

```kotlin
Scaffold(
    topBar = {
        TopAppBar(
            title = { Text("Заголовок") },
            navigationIcon = { IconButton(onClick = {}) { Icon(...) } },
            actions = { IconButton(onClick = {}) { Icon(...) } }
        )
    },
    bottomBar = {
        BottomNavigation {
            BottomNavigationItem(
                icon = { Icon(Icons.Default.Home, null) },
                label = { Text("Главная") },
                selected = true,
                onClick = {}
            )
        }
    },
    floatingActionButton = {
        FloatingActionButton(onClick = {}) {
            Icon(Icons.Default.Add, null)
        }
    }
) { paddingValues ->
    // ⭐ ВСЕГДА применяйте paddingValues!
    Column(Modifier.padding(paddingValues)) {
        Text("Контент")
    }
}
```

**Что такое Scaffold:**
- Стандартная структура Material Design экрана
- Слоты: `topBar`, `bottomBar`, `floatingActionButton`, `snackbarHost`, `content`
- Автоматически управляет отступами между элементами
- Аналог: CoordinatorLayout + AppBarLayout + BottomNavigationView

---

## Модификаторы (Modifier)

```kotlin
Modifier
    // Размеры
    .size(100.dp)
    .fillMaxWidth()
    .fillMaxHeight()
    .fillMaxSize()
    .width(100.dp)
    .height(100.dp)
    
    // Отступы
    .padding(16.dp)
    .padding(horizontal = 16.dp, vertical = 8.dp)
    
    // Фон и границы
    .background(Color.Red)
    .background(Color.Blue, RoundedCornerShape(8.dp))
    .border(2.dp, Color.Black, RoundedCornerShape(8.dp))
    
    // Клики
    .clickable { }
    
    // Вес (как в LinearLayout)
    .weight(1f)
    
    // Прокрутка
    .verticalScroll(rememberScrollState())
    .horizontalScroll(rememberScrollState())
```

**⚠️ Порядок модификаторов важен!**

---

## UI компоненты

### Text (TextView)
```kotlin
Text(
    text = "Текст",
    color = Color.Black,
    fontSize = 20.sp,
    fontWeight = FontWeight.Bold,
    maxLines = 2,
    overflow = TextOverflow.Ellipsis,
    style = MaterialTheme.typography.headlineMedium
)
```

### Button
```kotlin
Button(onClick = {}) { Text("Кнопка") }
OutlinedButton(onClick = {}) { Text("Outlined") }
TextButton(onClick = {}) { Text("Text") }
IconButton(onClick = {}) { Icon(...) }
```

### TextField (EditText)
```kotlin
var text by remember { mutableStateOf("") }

TextField(
    value = text,
    onValueChange = { text = it },
    label = { Text("Метка") },
    placeholder = { Text("Placeholder") },
    leadingIcon = { Icon(...) },
    singleLine = true
)

OutlinedTextField(value = text, onValueChange = { text = it })
```

### Image
```kotlin
Image(
    painter = painterResource(R.drawable.image),
    contentDescription = "Описание",
    contentScale = ContentScale.Crop
)

Icon(
    imageVector = Icons.Default.Favorite,
    contentDescription = null,
    tint = Color.Red
)
```

### Card
```kotlin
Card(
    modifier = Modifier.fillMaxWidth(),
    elevation = CardDefaults.cardElevation(4.dp),
    shape = RoundedCornerShape(12.dp)
) {
    Column(Modifier.padding(16.dp)) {
        Text("Заголовок")
        Text("Контент")
    }
}
```

### Checkbox, Switch, RadioButton
```kotlin
var checked by remember { mutableStateOf(false) }

Checkbox(checked = checked, onCheckedChange = { checked = it })
Switch(checked = checked, onCheckedChange = { checked = it })
RadioButton(selected = checked, onClick = { checked = true })
```

### Spacer, Divider
```kotlin
Spacer(Modifier.height(16.dp))  // вертикальный отступ
Spacer(Modifier.width(16.dp))   // горизонтальный отступ
Divider(thickness = 1.dp, color = Color.Gray)
```

---

## State Management

### remember
```kotlin
var count by remember { mutableStateOf(0) }
```

### rememberSaveable (сохраняется при повороте)
```kotlin
var count by rememberSaveable { mutableStateOf(0) }
```

### State Hoisting
```kotlin
@Composable
fun Parent() {
    var count by remember { mutableStateOf(0) }
    Child(count = count, onIncrement = { count++ })
}

@Composable
fun Child(count: Int, onIncrement: () -> Unit) {
    Button(onClick = onIncrement) { Text("Count: $count") }
}
```

---

## Side Effects

### LaunchedEffect (запуск корутины)
```kotlin
LaunchedEffect(userId) {
    data = loadUserData(userId)
}
```

### DisposableEffect (очистка ресурсов)
```kotlin
DisposableEffect(Unit) {
    val listener = LocationListener()
    locationManager.addListener(listener)
    onDispose { locationManager.removeListener(listener) }
}
```

---

## Navigation

```kotlin
val navController = rememberNavController()

NavHost(navController, startDestination = "home") {
    composable("home") {
        HomeScreen(onNavigate = { navController.navigate("details/$id") })
    }
    composable("details/{id}") { backStackEntry ->
        val id = backStackEntry.arguments?.getString("id")
        DetailsScreen(id)
    }
}
```

---

## ViewModel

```kotlin
class UserViewModel : ViewModel() {
    private val _users = MutableStateFlow<List<User>>(emptyList())
    val users: StateFlow<List<User>> = _users.asStateFlow()
}

@Composable
fun UserScreen(viewModel: UserViewModel = viewModel()) {
    val users by viewModel.users.collectAsState()
    
    LazyColumn {
        items(users) { UserItem(it) }
    }
}
```

---

## Темы (Material 3)

```kotlin
MaterialTheme(
    colorScheme = lightColorScheme(
        primary = Color(0xFF6200EE),
        secondary = Color(0xFF03DAC5)
    ),
    typography = Typography(...),
    shapes = Shapes(...)
) {
    // Приложение
}

// Использование
Text(
    text = "Текст",
    style = MaterialTheme.typography.headlineMedium,
    color = MaterialTheme.colorScheme.primary
)
```

---

## Сравнительная таблица: XML → Compose

| XML | Compose |
|-----|---------|
| `LinearLayout` (vertical) | `Column` |
| `LinearLayout` (horizontal) | `Row` |
| `FrameLayout` | `Box` |
| `RecyclerView` | `LazyColumn`, `LazyRow` |
| `GridLayoutManager` | `LazyVerticalGrid` |
| `ConstraintLayout` | `ConstraintLayout` |
| `CoordinatorLayout` | `Scaffold` |
| `TextView` | `Text` |
| `EditText` | `TextField` |
| `Button` | `Button` |
| `ImageView` | `Image` |
| `CardView` | `Card` |
| `ScrollView` | `Column` + `verticalScroll()` |
| `View.GONE` | `if (visible) { }` |
| `layout_weight` | `Modifier.weight()` |
| `android:padding` | `Modifier.padding()` |

---

## Ключевые вопросы для интервью

### 1. Что такое Composable функция?
> Функция с `@Composable`, описывающая UI. Вызывается при рекомпозиции.

### 2. Что такое Recomposition?
> Повторный вызов composable функций при изменении состояния.

### 3. remember vs rememberSaveable?
> `remember` - сохраняет при рекомпозиции.
> `rememberSaveable` - сохраняет при пересоздании Activity (поворот).

### 4. Что такое State Hoisting?
> Подъём состояния в родительский компонент. Дочерний получает значение и callback.

### 5. Зачем нужен Modifier?
> Настройка внешнего вида и поведения (размер, отступы, клики). Аналог XML атрибутов.

### 6. LazyColumn vs Column с verticalScroll?
> `LazyColumn` - ленивая загрузка (как RecyclerView).
> `Column + verticalScroll` - все элементы сразу (как ScrollView).

### 7. Что такое Scaffold?
> Контейнер для стандартной структуры Material Design экрана. Слоты для TopBar, BottomBar, FAB. Автоматически управляет отступами.

### 8. Порядок модификаторов важен?
> Да! `padding().background()` ≠ `background().padding()`

### 9. Как скрыть элемент (аналог View.GONE)?
> Условный рендеринг: `if (isVisible) { Text("Текст") }`

### 10. Преимущества Compose над XML?
> - Меньше boilerplate
> - Декларативный подход
> - Лучшая переиспользуемость
> - Типобезопасность
> - Проще работа с состоянием

---

## Важные зависимости

```kotlin
// build.gradle.kts (app)
dependencies {
    // Compose BOM
    implementation(platform("androidx.compose:compose-bom:2023.10.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
    debugImplementation("androidx.compose.ui:ui-tooling")
    
    // Activity Compose
    implementation("androidx.activity:activity-compose:1.8.0")
    
    // ViewModel
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.6.2")
    
    // Navigation
    implementation("androidx.navigation:navigation-compose:2.7.5")
    
    // Coil (загрузка изображений)
    implementation("io.coil-kt:coil-compose:2.5.0")
}
```

---

## Полезные паттерны

### Условный рендеринг
```kotlin
if (isLoading) {
    CircularProgressIndicator()
} else {
    Content()
}
```

### Список с разделителями
```kotlin
LazyColumn {
    items(list.size) { index ->
        Item(list[index])
        if (index < list.lastIndex) {
            Divider()
        }
    }
}
```

### Pull to Refresh
```kotlin
val refreshing by viewModel.isRefreshing.collectAsState()

PullRefreshIndicator(
    refreshing = refreshing,
    onRefresh = { viewModel.refresh() }
) {
    LazyColumn { ... }
}
```

### Диалог
```kotlin
var showDialog by remember { mutableStateOf(false) }

if (showDialog) {
    AlertDialog(
        onDismissRequest = { showDialog = false },
        title = { Text("Заголовок") },
        text = { Text("Текст") },
        confirmButton = {
            TextButton(onClick = { showDialog = false }) {
                Text("OK")
            }
        }
    )
}
```
