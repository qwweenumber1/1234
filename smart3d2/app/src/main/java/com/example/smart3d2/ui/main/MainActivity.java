package com.example.smart3d2;

import android.content.Intent;
import android.os.Bundle;

import androidx.appcompat.app.AppCompatActivity;

import com.example.smart3d2.data.storage.TokenStorage;
import com.example.smart3d2.ui.login.LoginActivity;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        TokenStorage tokenStorage = new TokenStorage(this);

        if (!tokenStorage.hasTokens()) {
            // ❌ нет токенов → логин
            startActivity(new Intent(this, LoginActivity.class));
            finish();
            return;
        }

        // ✅ есть токены → основной экран
        setContentView(R.layout.activity_main);
    }
}
