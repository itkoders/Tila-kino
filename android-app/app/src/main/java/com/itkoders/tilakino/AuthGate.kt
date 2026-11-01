package com.itkoders.tilakino

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
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
import com.google.firebase.auth.UserProfileChangeRequest

@Composable
fun AuthGate() {
    val auth = remember { FirebaseAuth.getInstance() }
    var currentUser by remember { mutableStateOf(auth.currentUser) }

    DisposableEffect(auth) {
        val listener = FirebaseAuth.AuthStateListener { firebaseAuth ->
            currentUser = firebaseAuth.currentUser
        }
        auth.addAuthStateListener(listener)
        onDispose { auth.removeAuthStateListener(listener) }
    }

    if (currentUser == null) {
        AuthScreen(auth = auth)
    } else {
        TilaKinoApp()
    }
}

@Composable
private fun AuthScreen(auth: FirebaseAuth) {
    var isRegister by remember { mutableStateOf(true) }
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var confirmPassword by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf("") }
    var isError by remember { mutableStateOf(false) }

    val gold = Color(0xFFFFC857)
    val muted = Color(0xFF9AA7B8)

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                brush = Brush.linearGradient(
                    colors = listOf(
                        Color(0xFF080B12),
                        Color(0xFF142536),
                        Color(0xFF080B12)
                    )
                )
            )
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(13.dp)
        ) {
            Text(
                text = "TILAKINO",
                color = gold,
                fontSize = 32.sp,
                fontWeight = FontWeight.Black
            )
            Text(
                text = "Davom etish uchun hisobingizga kiring",
                color = muted
            )

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(
                    onClick = {
                        isRegister = true
                        message = ""
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isRegister) gold else Color(0xFF121925),
                        contentColor = if (isRegister) Color.Black else Color.White
                    )
                ) {
                    Text("Ro‘yxatdan o‘tish")
                }

                OutlinedButton(
                    onClick = {
                        isRegister = false
                        message = ""
                    }
                ) {
                    Text("Kirish")
                }
            }

            if (isRegister) {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Ismingiz") },
                    singleLine = true
                )
            }

            OutlinedTextField(
                value = email,
                onValueChange = { email = it.trim() },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Email") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email)
            )

            OutlinedTextField(
                value = password,
                onValueChange = { password = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Parol (kamida 6 belgi)") },
                singleLine = true,
                visualTransformation = PasswordVisualTransformation()
            )

            if (isRegister) {
                OutlinedTextField(
                    value = confirmPassword,
                    onValueChange = { confirmPassword = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Parolni takrorlang") },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation()
                )
            }

            if (message.isNotBlank()) {
                Text(
                    text = message,
                    color = if (isError) Color(0xFFFF7777) else Color(0xFF45D7E8),
                    fontSize = 12.sp
                )
            }

            Button(
                onClick = {
                    message = ""
                    when {
                        !email.contains("@") || password.length < 6 -> {
                            isError = true
                            message = "Email yoki parol noto‘g‘ri. Parol kamida 6 belgi bo‘lsin."
                        }
                        isRegister && name.isBlank() -> {
                            isError = true
                            message = "Ismingizni kiriting."
                        }
                        isRegister && password != confirmPassword -> {
                            isError = true
                            message = "Parollar mos emas."
                        }
                        else -> {
                            isLoading = true
                            val authTask = if (isRegister) {
                                auth.createUserWithEmailAndPassword(email, password)
                            } else {
                                auth.signInWithEmailAndPassword(email, password)
                            }

                            authTask.addOnCompleteListener { result ->
                                if (result.isSuccessful) {
                                    if (isRegister) {
                                        val profile = UserProfileChangeRequest.Builder()
                                            .setDisplayName(name.trim())
                                            .build()
                                        auth.currentUser?.updateProfile(profile)
                                    }
                                    isError = false
                                    message = ""
                                } else {
                                    isError = true
                                    message = when (result.exception) {
                                        is FirebaseAuthUserCollisionException ->
                                            "Bu email avval ro‘yxatdan o‘tgan. Kirish bo‘limini tanlang."
                                        else -> result.exception?.localizedMessage
                                            ?: "Xatolik. Internet va Firebase sozlamalarini tekshiring."
                                    }
                                }
                                isLoading = false
                            }
                        }
                    }
                },
                enabled = !isLoading,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = gold,
                    contentColor = Color(0xFF080B12)
                ),
                shape = RoundedCornerShape(14.dp)
            ) {
                Text(
                    text = when {
                        isLoading -> "Kuting..."
                        isRegister -> "Hisob yaratish"
                        else -> "Kirish"
                    },
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = "Ro‘yxatdan o‘tmasdan ilovaga kirish mumkin emas.",
                color = muted,
                fontSize = 11.sp
            )
        }
    }
}
