package com.itkoders.tilakino

import android.content.Intent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AlternateEmail
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Mail
import androidx.compose.material.icons.filled.Movie
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Divider
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.common.api.ApiException
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseAuthUserCollisionException
import com.google.firebase.auth.GoogleAuthProvider
import com.google.firebase.auth.UserProfileChangeRequest

private val AuthInk = Color(0xFF070A12)
private val AuthPanel = Color(0xFF151B28)
private val AuthGold = Color(0xFFFFC857)
private val AuthCyan = Color(0xFF43D9E8)
private val AuthMuted = Color(0xFF9AA7B8)

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
    val context = androidx.compose.ui.platform.LocalContext.current
    var isRegister by remember { mutableStateOf(true) }
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var confirmPassword by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf("") }
    var isError by remember { mutableStateOf(false) }

    val googleLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        try {
            val account = GoogleSignIn.getSignedInAccountFromIntent(result.data)
                .getResult(ApiException::class.java)
            val token = account.idToken
            if (token.isNullOrBlank()) {
                isError = true
                message = "Google token olinmadi. Firebase Google sozlamasini tekshiring."
            } else {
                isLoading = true
                val credential = GoogleAuthProvider.getCredential(token, null)
                auth.signInWithCredential(credential).addOnCompleteListener { task ->
                    isLoading = false
                    if (!task.isSuccessful) {
                        isError = true
                        message = task.exception?.localizedMessage ?: "Google orqali kirishda xatolik."
                    }
                }
            }
        } catch (e: Exception) {
            isLoading = false
            isError = true
            message = when (e) {
                is com.google.android.gms.common.api.ApiException ->
                    if (e.statusCode == 12501) "Google orqali kirish bekor qilindi."
                    else "Google orqali kirib bo‘lmadi. Firebase sozlamasini tekshiring."
                else -> e.localizedMessage ?: "Google orqali kirishda xatolik."
            }
        }
    }

    fun startGoogleSignIn() {
        val resourceId = context.resources.getIdentifier(
            "default_web_client_id", "string", context.packageName
        )
        if (resourceId == 0) {
            isError = true
            message = "Google kirishi hali sozlanmagan: Firebase’dan yangilangan google-services.json kerak."
            return
        }
        val webClientId = context.getString(resourceId)
        val options = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestEmail()
            .requestIdToken(webClientId)
            .build()
        isLoading = true
        googleLauncher.launch(GoogleSignIn.getClient(context, options).signInIntent)
    }

    Box(
        modifier = Modifier.fillMaxSize().background(
            Brush.verticalGradient(
                listOf(Color(0xFF101C2B), AuthInk, Color(0xFF080B13), Color(0xFF171323))
            )
        ),
        contentAlignment = Alignment.Center
    ) {
        Column(
            modifier = Modifier.fillMaxWidth().verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp, vertical = 28.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Spacer(Modifier.height(8.dp))
            Box(
                modifier = Modifier.size(82.dp).clip(RoundedCornerShape(26.dp))
                    .background(Brush.linearGradient(listOf(AuthGold, Color(0xFFB87922)))),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Filled.Movie, contentDescription = "TILAKINO", tint = AuthInk, modifier = Modifier.size(43.dp))
            }
            Text("TILAKINO", color = Color.White, fontSize = 31.sp, fontWeight = FontWeight.Black, letterSpacing = 3.sp)
            Text("Kino olamiga xush kelibsiz", color = AuthCyan, fontSize = 13.sp, fontWeight = FontWeight.Medium)
            Text(
                "Sevimli filmlaringiz, seriallaringiz va yangi premyeralar — barchasi bir joyda.",
                color = AuthMuted, fontSize = 12.sp, textAlign = TextAlign.Center, lineHeight = 18.sp
            )

            Surface(
                modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                shape = RoundedCornerShape(26.dp),
                color = AuthPanel.copy(alpha = 0.96f),
                tonalElevation = 5.dp
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(13.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).background(AuthInk).padding(4.dp),
                        horizontalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        Button(
                            onClick = { isRegister = true; message = "" },
                            modifier = Modifier.weight(1f),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (isRegister) AuthGold else AuthInk,
                                contentColor = if (isRegister) AuthInk else AuthMuted
                            ),
                            shape = RoundedCornerShape(11.dp)
                        ) { Text("Ro‘yxatdan o‘tish", fontSize = 12.sp, fontWeight = FontWeight.Bold) }
                        Button(
                            onClick = { isRegister = false; message = "" },
                            modifier = Modifier.weight(1f),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (!isRegister) AuthGold else AuthInk,
                                contentColor = if (!isRegister) AuthInk else AuthMuted
                            ),
                            shape = RoundedCornerShape(11.dp)
                        ) { Text("Kirish", fontSize = 12.sp, fontWeight = FontWeight.Bold) }
                    }

                    Text(
                        if (isRegister) "Yangi hisob yarating" else "Hisobingizga kiring",
                        color = Color.White, fontSize = 19.sp, fontWeight = FontWeight.Bold
                    )

                    if (isRegister) {
                        AuthField(value = name, onValueChange = { name = it }, label = "Ismingiz", icon = {
                            Icon(Icons.Filled.Person, contentDescription = null)
                        })
                    }
                    AuthField(
                        value = email, onValueChange = { email = it.trim() },
                        label = "Elektron pochta", icon = { Icon(Icons.Filled.Mail, contentDescription = null) },
                        keyboardType = KeyboardType.Email
                    )
                    AuthField(
                        value = password, onValueChange = { password = it },
                        label = "Parol (kamida 6 belgi)", icon = { Icon(Icons.Filled.Lock, contentDescription = null) },
                        password = true
                    )
                    if (isRegister) {
                        AuthField(
                            value = confirmPassword, onValueChange = { confirmPassword = it },
                            label = "Parolni takrorlang", icon = { Icon(Icons.Filled.Lock, contentDescription = null) },
                            password = true
                        )
                    }

                    if (message.isNotBlank()) {
                        Text(message, color = if (isError) Color(0xFFFF8585) else AuthCyan, fontSize = 12.sp, lineHeight = 17.sp)
                    }

                    Button(
                        onClick = {
                            message = ""
                            when {
                                !email.contains("@") || password.length < 6 -> {
                                    isError = true
                                    message = "Emailni va kamida 6 belgili parolni kiriting."
                                }
                                isRegister && name.isBlank() -> {
                                    isError = true
                                    message = "Ismingizni kiriting."
                                }
                                isRegister && password != confirmPassword -> {
                                    isError = true
                                    message = "Parollar mos kelmadi."
                                }
                                else -> {
                                    isLoading = true
                                    val task = if (isRegister) auth.createUserWithEmailAndPassword(email, password)
                                    else auth.signInWithEmailAndPassword(email, password)
                                    task.addOnCompleteListener { result ->
                                        isLoading = false
                                        if (result.isSuccessful) {
                                            if (isRegister) {
                                                val profile = UserProfileChangeRequest.Builder()
                                                    .setDisplayName(name.trim()).build()
                                                auth.currentUser?.updateProfile(profile)
                                            }
                                            message = ""
                                        } else {
                                            isError = true
                                            message = when (result.exception) {
                                                is FirebaseAuthUserCollisionException -> "Bu email avval ro‘yxatdan o‘tgan. Kirish bo‘limini tanlang."
                                                else -> result.exception?.localizedMessage ?: "Kirishda xatolik. Internetni tekshiring."
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        enabled = !isLoading,
                        modifier = Modifier.fillMaxWidth().height(52.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AuthGold, contentColor = AuthInk),
                        shape = RoundedCornerShape(14.dp)
                    ) {
                        if (isLoading) CircularProgressIndicator(modifier = Modifier.size(19.dp), color = AuthInk, strokeWidth = 2.dp)
                        else {
                            Text(if (isRegister) "Hisob yaratish" else "Kirish", fontWeight = FontWeight.Bold)
                            Spacer(Modifier.size(8.dp))
                            Icon(Icons.Filled.ArrowForward, contentDescription = null)
                        }
                    }

                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Divider(modifier = Modifier.weight(1f), color = Color(0xFF343C4B))
                        Text("  YOKI  ", color = AuthMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                        Divider(modifier = Modifier.weight(1f), color = Color(0xFF343C4B))
                    }

                    OutlinedButtonGoogle(
                        enabled = !isLoading,
                        onClick = { startGoogleSignIn() }
                    )

                    Text(
                        "Google yoki email orqali kiring. Mehmon rejimi mavjud emas.",
                        color = AuthMuted, fontSize = 10.sp, textAlign = TextAlign.Center,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
            Text("Xavfsiz kirish • TILAKINO", color = Color(0xFF657286), fontSize = 10.sp)
        }
    }
}

@Composable
private fun AuthField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    icon: @Composable () -> Unit,
    keyboardType: KeyboardType = KeyboardType.Text,
    password: Boolean = false
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = Modifier.fillMaxWidth(),
        label = { Text(label, fontSize = 12.sp) },
        leadingIcon = icon,
        singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = keyboardType),
        visualTransformation = if (password) PasswordVisualTransformation() else androidx.compose.ui.text.input.VisualTransformation.None,
        shape = RoundedCornerShape(14.dp),
        colors = OutlinedTextFieldDefaults.colors(
            focusedBorderColor = AuthGold,
            unfocusedBorderColor = Color(0xFF394252),
            focusedLabelColor = AuthGold,
            cursorColor = AuthGold,
            focusedTextColor = Color.White,
            unfocusedTextColor = Color.White,
            focusedLeadingIconColor = AuthCyan,
            unfocusedLeadingIconColor = AuthMuted
        )
    )
}

@Composable
private fun OutlinedButtonGoogle(enabled: Boolean, onClick: () -> Unit) {
    androidx.compose.material3.OutlinedButton(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier.fillMaxWidth().height(50.dp),
        shape = RoundedCornerShape(14.dp),
        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White)
    ) {
        Text("G", color = Color(0xFF4285F4), fontSize = 20.sp, fontWeight = FontWeight.Black)
        Spacer(Modifier.size(10.dp))
        Text("Google bilan davom etish", fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
    }
}
