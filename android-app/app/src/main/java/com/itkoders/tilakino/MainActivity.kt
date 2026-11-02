package com.itkoders.tilakino

import android.os.Bundle
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import androidx.compose.ui.platform.LocalContext
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.animation.core.tween
import androidx.compose.ui.layout.ContentScale
import coil.compose.AsyncImage
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BookmarkBorder
import androidx.compose.material.icons.filled.Explore
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.LocalFireDepartment
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private val Ink = Color(0xFF080B12)
private val Panel = Color(0xFF121925)
private val Gold = Color(0xFFFFC857)
private val Cyan = Color(0xFF45D7E8)
private val Muted = Color(0xFF9AA7B8)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = darkColorScheme(
                primary = Gold,
                secondary = Cyan,
                background = Ink,
                surface = Panel,
                onPrimary = Ink,
                onBackground = Color.White,
                onSurface = Color.White
            )) {
                AuthGate()
            }
        }
    }
}

private data class Film(
    val title: String,
    val genre: String,
    val year: String,
    val rating: String,
    val accent: Color,
    val symbol: String,
    val code: String = "",
    val kind: String = "movie",
    val description: String = "",
    val posterUrl: String? = null
)

private val heroImages = listOf("https://image.tmdb.org/t/p/w1280/8bcoR3h5q3SF0MzslsqM8DPyX.jpg", "https://image.tmdb.org/t/p/w1280/5hoS3nEkGGXUfmnu39AR3aev3b8.jpg", "https://image.tmdb.org/t/p/w1280/7RyHsO4yDXtBv1zUU3mTpHeQ0d5.jpg")

private val films = emptyList<Film>()


private const val API_BASE_URL = "https://tilakino-telegram-bot.onrender.com"

private suspend fun loadCatalog(search: String): List<Film> = withContext(Dispatchers.IO) {
    val encoded = java.net.URLEncoder.encode(search, "UTF-8")
    val endpoint = "$API_BASE_URL/api/catalog?page=0" + if (search.isBlank()) "" else "&q=$encoded"
    val connection = (URL(endpoint).openConnection() as HttpURLConnection).apply {
        requestMethod = "GET"
        connectTimeout = 12000
        readTimeout = 15000
        setRequestProperty("Accept", "application/json")
    }
    try {
        if (connection.responseCode !in 200..299) throw IllegalStateException("Server javobi: ${connection.responseCode}")
        val body = connection.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
        val items = JSONObject(body).optJSONArray("items") ?: org.json.JSONArray()
        buildList {
            for (i in 0 until items.length()) {
                val item = items.optJSONObject(i) ?: continue
                val code = item.optString("code")
                val kind = item.optString("kind", "movie")
                val poster = item.optString("poster").takeIf { it.isNotBlank() && it != "null" }
                add(Film(
                    title = item.optString("title", "Nomsiz kino"),
                    genre = item.optString("genre", "Janr ko‘rsatilmagan"),
                    year = item.optString("year", ""),
                    rating = item.optString("rating", "0"),
                    accent = if (kind == "series") Color(0xFF315B78) else Color(0xFF684A78),
                    symbol = if (kind == "series") "▶" else "✦",
                    code = code,
                    kind = kind,
                    description = item.optString("description", ""),
                    posterUrl = poster?.let { "$API_BASE_URL$it" }
                ))
            }
        }
    } finally {
        connection.disconnect()
    }
}

@Composable
fun TilaKinoApp(userEmail: String?) {
    val context = LocalContext.current
    val preferences = remember { context.getSharedPreferences("tilakino_local", android.content.Context.MODE_PRIVATE) }
    var selectedTab by remember { mutableIntStateOf(0) }
    var catalogFilms by remember { mutableStateOf(films) }
    var catalogError by remember { mutableStateOf<String?>(null) }
    var catalogLoading by remember { mutableStateOf(true) }
    var query by remember { mutableStateOf("") }
    var selectedFilm by remember { mutableStateOf<Film?>(null) }
    var favorites by remember {
        mutableStateOf(preferences.getStringSet("favorite_titles", emptySet())?.toSet() ?: emptySet())
    }
    val toggleFavorite: (Film) -> Unit = { film ->
        val updated = favorites.toMutableSet().apply {
            if (contains(film.title)) remove(film.title) else add(film.title)
        }.toSet()
        favorites = updated
        preferences.edit().putStringSet("favorite_titles", updated).apply()
    }
    LaunchedEffect(query) {
        kotlinx.coroutines.delay(300)
        catalogLoading = true
        catalogError = null
        try {
            catalogFilms = loadCatalog(query)
        } catch (e: Exception) {
            catalogError = e.message ?: "Katalogni yuklab bo‘lmadi"
        } finally {
            catalogLoading = false
        }
    }
    val filteredFilms = catalogFilms

    Scaffold(
        containerColor = Ink,
        bottomBar = {
            NavigationBar(containerColor = Color(0xFF0D131D), contentColor = Gold) {
                val tabs = listOf(
                    "Bosh sahifa" to Icons.Filled.Home,
                    "Katalog" to Icons.Filled.Explore,
                    "Saqlangan" to Icons.Filled.BookmarkBorder,
                    "Profil" to Icons.Filled.Person
                )
                tabs.forEachIndexed { index, item ->
                    NavigationBarItem(
                        selected = selectedTab == index,
                        onClick = { selectedTab = index; selectedFilm = null },
                        icon = { Icon(item.second, contentDescription = item.first) },
                        label = { Text(item.first, fontSize = 10.sp) }
                    )
                }
            }
        }
    ) { padding ->
        if (selectedFilm != null) {
            FilmDetails(film = selectedFilm!!, modifier = Modifier.padding(padding), isFavorite = selectedFilm!!.title in favorites, onFavorite = { toggleFavorite(selectedFilm!!) }, onBack = { selectedFilm = null })
        } else {
            when (selectedTab) {
                0 -> HomeScreen(
                    modifier = Modifier.padding(padding),
                    query = query,
                    onQueryChange = { query = it },
                    onFilmClick = { selectedFilm = it },
                    visibleFilms = filteredFilms
                )
                1 -> CatalogScreen(Modifier.padding(padding), onFilmClick = { selectedFilm = it }, visibleFilms = filteredFilms)
                2 -> SavedScreen(Modifier.padding(padding), favorites = catalogFilms.filter { it.title in favorites }, onFilmClick = { selectedFilm = it })
                else -> ProfileScreen(Modifier.padding(padding), userEmail = userEmail, onSignOut = { com.google.firebase.auth.FirebaseAuth.getInstance().signOut() })
            }
        }
    }
}

@Composable
private fun HomeScreen(
    modifier: Modifier = Modifier,
    query: String,
    onQueryChange: (String) -> Unit,
    onFilmClick: (Film) -> Unit,
    visibleFilms: List<Film>
) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(22.dp)
    ) {
        item {
            Row(
                modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 18.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text("TILA", color = Color.White, fontSize = 25.sp, fontWeight = FontWeight.Black, letterSpacing = 2.sp)
                    Text("K I N O", color = Gold, fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 4.sp)
                }
                Surface(shape = CircleShape, color = Panel, modifier = Modifier.size(42.dp)) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(Icons.Filled.LocalFireDepartment, contentDescription = "Trend", tint = Gold)
                    }
                }
            }
        }
        item {
            OutlinedTextField(
                value = query,
                onValueChange = onQueryChange,
                modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp),
                singleLine = true,
                placeholder = { Text("Kino, aktyor yoki janrni qidiring", color = Muted, fontSize = 13.sp) },
                leadingIcon = { Icon(Icons.Filled.Search, contentDescription = "Qidirish", tint = Cyan) },
                shape = RoundedCornerShape(16.dp)
            )
        }
        item {
            HeroBanner(onClick = { visibleFilms.firstOrNull()?.let(onFilmClick) })
        }
        item {
            CategoryChips()
        }
        item {
            FilmSection(
                title = "Bugun trendda",
                subtitle = "Tomoshabinlar tanlovi",
                list = visibleFilms,
                onFilmClick = onFilmClick
            )
        }
        item {
            PremiumBanner()
        }
        item {
            FilmSection(
                title = "Siz uchun tanladik",
                subtitle = "Yangi taassurotlar",
                list = visibleFilms.reversed(),
                onFilmClick = onFilmClick
            )
        }
    }
}

@Composable
private fun HeroBanner(onClick: () -> Unit) {
    var slide by remember { mutableIntStateOf(0) }
    LaunchedEffect(Unit) {
        while (true) {
            kotlinx.coroutines.delay(5500)
            slide = (slide + 1) % heroImages.size
        }
    }
    Box(Modifier.fillMaxWidth().padding(horizontal = 16.dp).height(270.dp).clip(RoundedCornerShape(26.dp)).clickable(onClick = onClick)) {
        AnimatedContent(slide, transitionSpec = { fadeIn(tween(900)) togetherWith fadeOut(tween(900)) }, label = "home-hero") { index ->
            AsyncImage(model = heroImages[index], contentDescription = "Kino banneri", modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
        }
        Box(Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Color.Transparent, Color(0xEE05070D)))))
        Column(Modifier.align(Alignment.BottomStart).padding(20.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
            Text("TILAKINO ORIGINAL", color = Cyan, fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 2.sp)
            Text("KINO OLAMIGA XUSH KELIBSIZ", color = Color.White, fontSize = 25.sp, fontWeight = FontWeight.Black)
            Text("Har kuni yangi taassurotlar", color = Color.White.copy(alpha = .8f), fontSize = 11.sp)
            Button(onClick = onClick, colors = ButtonDefaults.buttonColors(containerColor = Gold, contentColor = Ink), shape = RoundedCornerShape(12.dp)) {
                Icon(Icons.Filled.PlayArrow, contentDescription = null); Spacer(Modifier.width(5.dp)); Text("Katalogni ko‘rish", fontWeight = FontWeight.Bold)
            }
        }
    }
}
@Composable
private fun CategoryChips() {
    val categories = listOf("Hammasi", "Kino", "Serial", "Anime", "Multfilm")
    Row(
        modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal = 16.dp),
        horizontalArrangement = Arrangement.spacedBy(9.dp)
    ) {
        categories.forEachIndexed { index, label ->
            Surface(
                color = if (index == 0) Gold else Panel,
                shape = RoundedCornerShape(50),
                modifier = Modifier.clip(RoundedCornerShape(50)).clickable { }
            ) {
                Text(label, color = if (index == 0) Ink else Color.White, modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp), fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
            }
        }
    }
}

@Composable
private fun FilmSection(
    title: String,
    subtitle: String,
    list: List<Film>,
    onFilmClick: (Film) -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Column(modifier = Modifier.padding(horizontal = 20.dp)) {
            Text(title, color = Color.White, fontSize = 19.sp, fontWeight = FontWeight.Bold)
            Text(subtitle, color = Muted, fontSize = 11.sp)
        }
        LazyRow(contentPadding = PaddingValues(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            items(list) { film ->
                FilmPoster(film = film, onClick = { onFilmClick(film) })
            }
        }
    }
}

@Composable
private fun FilmPoster(film: Film, onClick: () -> Unit) {
    Column(modifier = Modifier.width(142.dp).clickable(onClick = onClick), verticalArrangement = Arrangement.spacedBy(7.dp)) {
        Box(
            modifier = Modifier.fillMaxWidth().height(190.dp).clip(RoundedCornerShape(18.dp))
                .background(Brush.linearGradient(listOf(film.accent, Color(0xFF111827), Ink)))
        ) {
            if (film.posterUrl != null) AsyncImage(model = film.posterUrl, contentDescription = film.title, modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop) else Text(film.symbol, modifier = Modifier.align(Alignment.Center), color = Color.White.copy(alpha = 0.65f), fontSize = 64.sp)
            Surface(color = Color.Black.copy(alpha = 0.55f), shape = RoundedCornerShape(8.dp), modifier = Modifier.align(Alignment.TopEnd).padding(8.dp)) {
                Row(modifier = Modifier.padding(horizontal = 7.dp, vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Filled.Star, contentDescription = null, tint = Gold, modifier = Modifier.size(12.dp))
                    Text(film.rating, color = Color.White, fontSize = 10.sp)
                }
            }
            Text(film.year, modifier = Modifier.align(Alignment.BottomStart).padding(10.dp), color = Color.White.copy(alpha = 0.8f), fontSize = 10.sp)
        }
        Text(film.title, color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
        Text(film.genre, color = Muted, fontSize = 10.sp, maxLines = 1)
    }
}

@Composable
private fun PremiumBanner() {
    Row(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp).clip(RoundedCornerShape(20.dp))
            .background(Brush.horizontalGradient(listOf(Color(0xFF48351A), Color(0xFF171B26))))
            .padding(18.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Text("TILAKINO PREMIUM", color = Gold, fontSize = 10.sp, fontWeight = FontWeight.Black, letterSpacing = 1.5.sp)
            Text("Kino zavqi — cheksiz", color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.Bold)
            Text("Reklamasiz tomosha va yuqori sifat", color = Color.White.copy(alpha = 0.7f), fontSize = 10.sp)
        }
        Text("✦", color = Gold, fontSize = 38.sp)
    }
}

@Composable
private fun CatalogScreen(modifier: Modifier, onFilmClick: (Film) -> Unit, visibleFilms: List<Film>) {
    LazyColumn(modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        item { Text("Katalog", color = Color.White, fontSize = 28.sp, fontWeight = FontWeight.Black) }
        item { Text("Kino olamini kashf eting", color = Muted, fontSize = 13.sp) }
        items(visibleFilms) { film ->
            Row(
                modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Panel)
                    .clickable { onFilmClick(film) }.padding(10.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(Modifier.size(width = 76.dp, height = 96.dp).clip(RoundedCornerShape(12.dp)).background(film.accent), contentAlignment = Alignment.Center) {
                    if (film.posterUrl != null) AsyncImage(model = film.posterUrl, contentDescription = film.title, modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop) else Text(film.symbol, color = Color.White, fontSize = 30.sp)
                }
                Column(Modifier.weight(1f).padding(start = 13.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                    Text(film.title, color = Color.White, fontWeight = FontWeight.Bold)
                    Text("${film.year} · ${film.genre}", color = Muted, fontSize = 11.sp)
                    Text("★ ${film.rating}", color = Gold, fontSize = 12.sp)
                }
                Icon(Icons.Filled.PlayArrow, contentDescription = "Ochish", tint = Cyan)
            }
        }
    }
}

@Composable
private fun SavedScreen(modifier: Modifier, favorites: List<Film>, onFilmClick: (Film) -> Unit) {
    if (favorites.isEmpty()) {
        Box(modifier.fillMaxSize().padding(28.dp), contentAlignment = Alignment.Center) {
            Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Icon(Icons.Filled.BookmarkBorder, contentDescription = null, tint = Gold, modifier = Modifier.size(48.dp))
                Text("Saqlangan kinolar", color = Color.White, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                Text("Hozircha sevimlilarga kino qo‘shilmagan.", color = Muted, fontSize = 13.sp)
            }
        }
    } else {
        LazyColumn(modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item { Text("Sevimlilar", color = Color.White, fontSize = 26.sp, fontWeight = FontWeight.Black) }
            items(favorites) { film ->
                Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Panel).clickable { onFilmClick(film) }.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(58.dp).clip(RoundedCornerShape(12.dp)).background(film.accent), contentAlignment = Alignment.Center) {
                        if (film.posterUrl != null) AsyncImage(model = film.posterUrl, contentDescription = film.title, modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop) else Text(film.symbol, color = Color.White, fontSize = 26.sp)
                    }
                    Column(Modifier.weight(1f).padding(start = 12.dp)) {
                        Text(film.title, color = Color.White, fontWeight = FontWeight.Bold)
                        Text("${film.year} · ${film.genre}", color = Muted, fontSize = 11.sp)
                    }
                    Icon(Icons.Filled.BookmarkBorder, contentDescription = "Saqlangan", tint = Gold)
                }
            }
        }
    }
}

@Composable
private fun ProfileScreen(modifier: Modifier, userEmail: String?, onSignOut: () -> Unit) {
    val isAdmin = userEmail.equals("berdiqulv@gmail.com", ignoreCase = true)
    Column(modifier.fillMaxSize().padding(22.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        Text("Profil", color = Color.White, fontSize = 28.sp, fontWeight = FontWeight.Black)
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(13.dp)) {
            Surface(shape = CircleShape, color = Panel, modifier = Modifier.size(58.dp)) {
                Box(contentAlignment = Alignment.Center) { Icon(Icons.Filled.Person, contentDescription = null, tint = Gold, modifier = Modifier.size(30.dp)) }
            }
            Column(Modifier.weight(1f)) {
                Text(userEmail ?: "TILAKINO foydalanuvchisi", color = Color.White, fontWeight = FontWeight.Bold)
                Text(if (isAdmin) "ADMINISTRATOR" else "Faol hisob", color = if (isAdmin) Gold else Muted, fontSize = 12.sp)
            }
        }
        if (isAdmin) {
            Surface(color = Color(0xFF302515), shape = RoundedCornerShape(14.dp), modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("ADMIN HISOBI", color = Gold, fontWeight = FontWeight.Black)
                    Text("Administrator email tanildi. Boshqaruv serveri va xavfsiz admin ruxsatlari hali alohida sozlanishi kerak.", color = Color.White, fontSize = 12.sp)
                }
            }
        }
        Button(onClick = onSignOut, modifier = Modifier.fillMaxWidth(), colors = ButtonDefaults.buttonColors(containerColor = Gold, contentColor = Ink)) {
            Text("Hisobdan chiqish")
        }
        Text("Til: O‘zbekcha", color = Color.White)
        Text("Ilova versiyasi: 1.0.0", color = Muted, fontSize = 12.sp)
    }
}


@Composable
private fun FilmDetails(
    film: Film,
    modifier: Modifier = Modifier,
    isFavorite: Boolean,
    onFavorite: () -> Unit,
    onBack: () -> Unit
) {
    Column(
        modifier = modifier.fillMaxSize().background(Ink).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("‹  Orqaga", color = Gold, modifier = Modifier.clickable(onClick = onBack), fontWeight = FontWeight.Bold)
            Spacer(Modifier.weight(1f))
            Text("TILAKINO", color = Gold, fontWeight = FontWeight.Black, letterSpacing = 2.sp)
        }
        Box(
            Modifier.fillMaxWidth().height(250.dp).clip(RoundedCornerShape(22.dp))
                .background(Brush.linearGradient(listOf(film.accent, Panel, Ink))),
            contentAlignment = Alignment.Center
        ) {
            Text(film.symbol, color = Color.White, fontSize = 88.sp, fontWeight = FontWeight.Black)
            Surface(
                color = Color(0xCC080B12),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.align(Alignment.BottomStart).padding(12.dp)
            ) {
                Text("★ ${film.rating}  •  ${film.year}", color = Gold, modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp), fontSize = 12.sp)
            }
        }
        Text(film.title, color = Color.White, fontSize = 25.sp, fontWeight = FontWeight.Black)
        Text(film.genre, color = Cyan, fontSize = 13.sp)
        Text(if (film.description.isBlank()) "Tavsif mavjud emas." else film.description, color = Muted, fontSize = 13.sp)
        Text("Kino kodi: ${film.code}", color = Gold, fontSize = 12.sp)
        Button(
            onClick = onFavorite,
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(containerColor = if (isFavorite) Panel else Gold, contentColor = if (isFavorite) Gold else Ink)
        ) {
            Icon(Icons.Filled.BookmarkBorder, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text(if (isFavorite) "Saqlanganlardan olib tashlash" else "Sevimlilarga qo‘shish")
        }
    }
}
