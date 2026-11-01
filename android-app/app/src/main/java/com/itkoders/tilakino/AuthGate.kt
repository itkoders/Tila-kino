package com.itkoders.tilakino

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseAuthUserCollisionException

@Composable
fun AuthGate() {
    val auth = remember { FirebaseAuth.getInstance() }
    var user by remember { mutableStateOf(auth.currentUser) }
    DisposableEffect(auth) {
        val listener = FirebaseAuth.AuthStateListener { user = it.currentUser }
        auth.addAuthStateListener(listener)
        onDispose { auth.removeAuthStateListener(listener) }
    }
    if (user == null) AuthScreen(auth) else TilaKinoApp()
}

@Composable
private fun AuthScreen(auth: FirebaseAuth) {
    var register by remember { mutableStateOf(true) }
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var confirm by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf("") }
    var isError by remember { mutableStateOf(false) }

    Box(Modifier.fillMaxSize().background(Brush.linearGradient(listOf(Color(0xFF080B12), Color(0xFF142536), Color(0xFF080B12))).padding(24.dp), contentAlignment = Alignment.Center) {
        Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(13.dp)) {
            Text("TILAKINO", color = Color(0xFFFFC857), fontSize = 32.sp, fontWeight = FontWeight.Black)
            Text("Davom etish uchun hisobingizga kiring", color = Color(0xFF9AA7B8))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { register = true; message = "" }, colors = ButtonDefaults.buttonColors(containerColor = if (register) Color(0xFFFFC857) else Color(0xFF121925), contentColor = if (register) Color.Black else Color.White)) { Text("Ro‘yxatdan o‘tish") }
                OutlinedButton(onClick = { register = false; message = "" }) { Text("Kirish") }
            }
            if (register) OutlinedTextField(name, { name = it }, Modifier.fillMaxWidth(), label = { Text("Ismingiz") }, singleLine = true)
            OutlinedTextField(email, { email = it.trim() }, Modifier.fillMaxWidth(), label = { Text("Email") }, singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email))
            OutlinedTextField(password, { password = it }, Modifier.fillMaxWidth(), label = { Text("Parol (kamida 6 belgi)") }, singleLine = true, visualTransformation = PasswordVisualTransformation())
            if (register) OutlinedTextField(confirm, { confirm = it }, Modifier.fillMaxWidth(), label = { Text("Parolni takrorlang") }, singleLine = true, visualTransformation = PasswordVisualTransformation())
            if (message.isNotBlank()) Text(message, color = if (isError) Color(0xFFFF7777) else Color(0xFF45D7E8), fontSize = 12.sp)
            Button(
                onClick = {
                    message = ""
                    when {
                        !email.contains("@") || password.length < 6 -> { isError = true; message = "Email yoki parol noto‘g‘ri. Parol kamida 6 belgi bo‘lsin." }
                        register && name.isBlank() -> { isError = true; message = "Ismingizni kiriting." }
                        register && password != confirm -> { isError = true; message = "Parollar mos emas." }
                        else -> {
                            busy = true
                            val task = if (register) auth.createUserWithEmailAndPassword(email, password) else auth.signInWithEmailAndPassword(email, password)
                            task.addOnCompleteListener { result ->
                                busy = false
                                if (result.isSuccessful) {
                                    if (register) {
                                        val profile = com.google.firebase.auth.UserProfileChangeRequest.Builder().setDisplayName(name.trim()).build()
                                        auth.currentUser?.updateProfile(profile)
                                    }
                                } else {
                                    isError = true
                                    message = if (result.exception is FirebaseAuthUserCollisionException) "Bu email avval ro‘yxatdan o‘tgan. Kirish bo‘limini tanlang." else result.exception?.localizedMessage ?: "Xatolik. Internet va Firebase sozlamalarini tekshiring."
                                }
                            }
                        }
                    }
                },
                enabled = !busy,
                modifier = Modifier.fillMaxWidth().height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFFC857), contentColor = Color(0xFF080B12)),
                shape = RoundedCornerShape(14.dp)
            ) { Text(if (busy) "Kuting..." else if (register) "Hisob yaratish" else "Kirish", fontWeight = FontWeight.Bold) }
            Text("Ro‘yxatdan o‘tmasdan ilovaga kirish mumkin emas.", color = Color(0xFF9AA7B8), fontSize = 11.sp)
        }
    }
}
