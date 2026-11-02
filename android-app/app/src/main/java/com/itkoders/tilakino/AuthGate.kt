package com.itkoders.tilakino

import android.app.Activity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.common.api.ApiException
import com.google.firebase.auth.*
import java.util.concurrent.TimeUnit

private val AuthInk = Color(0xFF070912)
private val AuthGold = Color(0xFFFFC247)
private val AuthMuted = Color(0xFFD0D3DC)
private val authBackdrops = listOf(
    "https://image.tmdb.org/t/p/w1280/8bcoR3h5q3SF0MzslsqM8DPyX明.jpg",
    "https://image.tmdb.org/t/p/w1280/5hoS3nEkGGXUfmnu39AR3aev3b8.jpg",
    "https://image.tmdb.org/t/p/w1280/7RyHsO4yDXtBv1zUU3mTpHeQ0d5.jpg",
    "https://image.tmdb.org/t/p/w1280/2u7zbn8EudG6kLlBzUYqP8Hj8x.jpg"
)

@Composable
fun AuthGate() {
    val auth = remember { FirebaseAuth.getInstance() }
    var currentUser by remember { mutableStateOf(auth.currentUser) }
    DisposableEffect(auth) {
        val listener = FirebaseAuth.AuthStateListener { currentUser = it.currentUser }
        auth.addAuthStateListener(listener)
        onDispose { auth.removeAuthStateListener(listener) }
    }
    if (currentUser == null) AuthScreen(auth) else TilaKinoApp()
}

@Composable
private fun AuthScreen(auth: FirebaseAuth) {
    val context = LocalContext.current
    var register by remember { mutableStateOf(true) }
    var method by remember { mutableStateOf("email") }
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var confirm by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("+998") }
    var smsCode by remember { mutableStateOf("") }
    var verificationId by remember { mutableStateOf<String?>(null) }
    var resendToken by remember { mutableStateOf<PhoneAuthProvider.ForceResendingToken?>(null) }
    var loading by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf("") }
    var error by remember { mutableStateOf(false) }
    var backdrop by remember { mutableIntStateOf(0) }

    LaunchedEffect(Unit) {
        while (true) {
            kotlinx.coroutines.delay(6500)
            backdrop = (backdrop + 1) % authBackdrops.size
        }
    }

    val googleLauncher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        try {
            val account = GoogleSignIn.getSignedInAccountFromIntent(result.data).getResult(ApiException::class.java)
            val token = account.idToken
            if (token.isNullOrBlank()) {
                loading = false; error = true; message = "Google token olinmadi. Firebase OAuth sozlamasini tekshiring."
            } else {
                auth.signInWithCredential(GoogleAuthProvider.getCredential(token, null)).addOnCompleteListener {
                    loading = false
                    if (!it.isSuccessful) { error = true; message = it.exception?.localizedMessage ?: "Google orqali kirishda xatolik." }
                }
            }
        } catch (e: Exception) {
            loading = false; error = true
            message = if (e is ApiException && e.statusCode == 12501) "Google kirishi bekor qilindi." else "Google kirishi amalga oshmadi. Firebase sozlamasini tekshiring."
        }
    }

    fun googleSignIn() {
        val id = context.resources.getIdentifier("default_web_client_id", "string", context.packageName)
        if (id == 0) { error = true; message = "Firebase Google OAuth sozlamasi talab qilinadi."; return }
        val options = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestEmail().requestIdToken(context.getString(id)).build()
        loading = true
        googleLauncher.launch(GoogleSignIn.getClient(context, options).signInIntent)
    }

    fun verifyPhone() {
        val activity = context as? Activity
        if (activity == null || !phone.startsWith("+") || phone.length < 10) {
            error = true; message = "Telefon raqamini xalqaro formatda kiriting. Masalan: +998901234567"; return
        }
        loading = true; message = ""
        val callbacks = object : PhoneAuthProvider.OnVerificationStateChangedCallbacks() {
            override fun onVerificationCompleted(credential: PhoneAuthCredential) {
                auth.signInWithCredential(credential).addOnCompleteListener {
                    loading = false
                    if (!it.isSuccessful) { error = true; message = it.exception?.localizedMessage ?: "Telefon tasdiqlanmadi." }
                }
            }
            override fun onVerificationFailed(e: FirebaseException) {
                loading = false; error = true
                message = when (e) {
                    is FirebaseAuthInvalidCredentialsException -> "Telefon raqami noto‘g‘ri."
                    is FirebaseTooManyRequestsException -> "SMS so‘rovlari limiti tugadi. Keyinroq urinib ko‘ring."
                    else -> e.localizedMessage ?: "SMS yuborilmadi. Firebase Phone Auth sozlamasini tekshiring."
                }
            }
            override fun onCodeSent(id: String, token: PhoneAuthProvider.ForceResendingToken) {
                loading = false; verificationId = id; resendToken = token
                error = false; message = "SMS kodi yuborildi. 6 xonali kodni kiriting."
            }
        }
        val builder = PhoneAuthOptions.newBuilder(auth).setPhoneNumber(phone.trim())
            .setTimeout(60L, TimeUnit.SECONDS).setActivity(activity).setCallbacks(callbacks)
        if (resendToken != null) builder.setForceResendingToken(resendToken!!)
        PhoneAuthProvider.verifyPhoneNumber(builder.build())
    }

    Box(Modifier.fillMaxSize().background(AuthInk)) {
        AnimatedContent(targetState = backdrop, transitionSpec = { androidx.compose.animation.fadeIn(tween(1100)) togetherWith androidx.compose.animation.fadeOut(tween(1100)) }, label = "cinema-backdrop") { index ->
            AsyncImage(model = authBackdrops[index], contentDescription = null, modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
        }
        Box(Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Color(0xAA03050B), Color(0xCC050710), Color(0xFF050710)))))
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 24.dp, vertical = 28.dp),
            horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center
        ) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                Surface(color = Color(0x88202735), shape = RoundedCornerShape(30.dp)) {
                    Text("🌐  O‘zbekcha", color = AuthGold, modifier = Modifier.padding(horizontal = 14.dp, vertical = 9.dp), fontSize = 12.sp)
                }
            }
            Spacer(Modifier.height(28.dp))
            Text("▶", color = AuthGold, fontSize = 64.sp, fontWeight = FontWeight.Black)
            Text("TILAKINO", color = Color.White, fontSize = 34.sp, fontWeight = FontWeight.Black, letterSpacing = 4.sp)
            Text("KINO OLAMI SIZ BILAN", color = AuthGold, fontSize = 11.sp, letterSpacing = 3.sp)
            Spacer(Modifier.height(26.dp))
            Surface(color = Color(0xCC0C101A), shape = RoundedCornerShape(26.dp), border = androidx.compose.foundation.BorderStroke(1.dp, AuthGold.copy(alpha = .55f))) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf("email" to "Email", "phone" to "Telefon").forEach { (key, label) ->
                            Button(onClick = { method = key; message = ""; verificationId = null }, modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.buttonColors(containerColor = if (method == key) AuthGold else Color(0xFF202633), contentColor = if (method == key) AuthInk else Color.White),
                                shape = RoundedCornerShape(12.dp)) { Text(label, fontWeight = FontWeight.Bold) }
                        }
                    }
                    if (method == "email") {
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { register = false; message = "" }, modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.buttonColors(containerColor = if (!register) AuthGold else Color(0xFF202633), contentColor = if (!register) AuthInk else Color.White),
                                shape = RoundedCornerShape(12.dp)) { Text("Kirish") }
                            Button(onClick = { register = true; message = "" }, modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.buttonColors(containerColor = if (register) AuthGold else Color(0xFF202633), contentColor = if (register) AuthInk else Color.White),
                                shape = RoundedCornerShape(12.dp)) { Text("Ro‘yxatdan o‘tish") }
                        }
                        if (register) AuthInput(name, { name = it }, "Ismingiz", KeyboardType.Text)
                        AuthInput(email, { email = it }, "Email manzilingiz", KeyboardType.Email)
                        AuthInput(password, { password = it }, "Parol (kamida 6 belgi)", KeyboardType.Password, true)
                        if (register) AuthInput(confirm, { confirm = it }, "Parolni takrorlang", KeyboardType.Password, true)
                        GoldAction(if (register) "Hisob yaratish" else "Kirish", loading) {
                            when {
                                !email.contains("@") || password.length < 6 -> { error = true; message = "Email va kamida 6 belgili parol kiriting." }
                                register && name.isBlank() -> { error = true; message = "Ismingizni kiriting." }
                                register && password != confirm -> { error = true; message = "Parollar mos emas." }
                                else -> {
                                    loading = true
                                    val task = if (register) auth.createUserWithEmailAndPassword(email.trim(), password) else auth.signInWithEmailAndPassword(email.trim(), password)
                                    task.addOnCompleteListener { result ->
                                        loading = false
                                        if (!result.isSuccessful) { error = true; message = result.exception?.localizedMessage ?: "Amal bajarilmadi." }
                                        else if (register) auth.currentUser?.updateProfile(UserProfileChangeRequest.Builder().setDisplayName(name.trim()).build())
                                    }
                                }
                            }
                        }
                        TextButton(onClick = { auth.sendPasswordResetEmail(email.trim()).addOnCompleteListener { message = if (it.isSuccessful) "Parolni tiklash havolasi emailingizga yuborildi." else "Emailni tekshiring va qayta urinib ko‘ring."; error = !it.isSuccessful } }) {
                            Text("Parolni unutdingizmi?", color = AuthGold)
                        }
                    } else {
                        AuthInput(phone, { phone = it.filter { c -> c.isDigit() || c == '+' } }, "Telefon: +998901234567", KeyboardType.Phone)
                        if (verificationId != null) AuthInput(smsCode, { smsCode = it.filter(Char::isDigit).take(6) }, "SMS kodi", KeyboardType.Number)
                        GoldAction(if (verificationId == null) "SMS kod yuborish" else "Kodni tasdiqlash", loading) {
                            if (verificationId == null) verifyPhone()
                            else {
                                if (smsCode.length != 6) { error = true; message = "6 xonali SMS kodni kiriting." }
                                else {
                                    loading = true
                                    val credential = PhoneAuthProvider.getCredential(verificationId!!, smsCode)
                                    auth.signInWithCredential(credential).addOnCompleteListener {
                                        loading = false
                                        if (!it.isSuccessful) { error = true; message = it.exception?.localizedMessage ?: "Kod noto‘g‘ri yoki muddati tugagan." }
                                    }
                                }
                            }
                        }
                        if (verificationId != null) TextButton(onClick = { verificationId = null; smsCode = ""; verifyPhone() }) { Text("Kodni qayta yuborish", color = AuthGold) }
                    }
                    if (message.isNotBlank()) Text(message, color = if (error) Color(0xFFFF8989) else Color(0xFF7DE7D5), fontSize = 12.sp, textAlign = TextAlign.Center)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        HorizontalDivider(Modifier.weight(1f), color = Color.Gray)
                        Text("  YOKI  ", color = AuthMuted, fontSize = 10.sp)
                        HorizontalDivider(Modifier.weight(1f), color = Color.Gray)
                    }
                    OutlinedButton(onClick = { googleSignIn() }, enabled = !loading, modifier = Modifier.fillMaxWidth().height(52.dp),
                        border = androidx.compose.foundation.BorderStroke(1.dp, AuthGold.copy(alpha = .8f)), shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White)) {
                        Text("G", color = Color(0xFF4285F4), fontSize = 22.sp, fontWeight = FontWeight.Black)
                        Spacer(Modifier.width(10.dp)); Text("Google bilan davom etish", fontWeight = FontWeight.Bold)
                    }
                    Text("Xavfsiz kirish • Mehmon rejimi yo‘q", color = AuthMuted, fontSize = 10.sp, modifier = Modifier.fillMaxWidth(), textAlign = TextAlign.Center)
                }
            }
            Spacer(Modifier.height(22.dp))
            Text("✦  PREMIUM  •  YANGI KINOLAR  •  HD SIFAT", color = AuthGold, fontSize = 10.sp, letterSpacing = 1.sp, textAlign = TextAlign.Center)
        }
    }
}

@Composable
private fun AuthInput(value: String, onChange: (String) -> Unit, label: String, type: KeyboardType, secret: Boolean = false) {
    OutlinedTextField(value, onChange, modifier = Modifier.fillMaxWidth(), label = { Text(label, fontSize = 12.sp) },
        singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = type),
        visualTransformation = if (secret) PasswordVisualTransformation() else androidx.compose.ui.text.input.VisualTransformation.None,
        shape = RoundedCornerShape(14.dp),
        colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = AuthGold, unfocusedBorderColor = Color(0xFF687080),
            focusedLabelColor = AuthGold, cursorColor = AuthGold, focusedTextColor = Color.White, unfocusedTextColor = Color.White))
}

@Composable
private fun GoldAction(label: String, loading: Boolean, onClick: () -> Unit) {
    Button(onClick = onClick, enabled = !loading, modifier = Modifier.fillMaxWidth().height(52.dp),
        colors = ButtonDefaults.buttonColors(containerColor = AuthGold, contentColor = AuthInk), shape = RoundedCornerShape(14.dp)) {
        if (loading) CircularProgressIndicator(Modifier.size(20.dp), color = AuthInk, strokeWidth = 2.dp)
        else Text(label, fontWeight = FontWeight.Black)
    }
}
