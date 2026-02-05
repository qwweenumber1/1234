package com.example.smart3d2.ui.login;

import android.os.Bundle;
import android.util.Log;

import androidx.appcompat.app.AppCompatActivity;

import com.example.smart3d2.R;
import com.example.smart3d2.data.api.ApiProvider;
import com.example.smart3d2.data.storage.TokenStorage;

import org.openapitools.client.ApiCallback;
import org.openapitools.client.ApiException;
import org.openapitools.client.api.DefaultApi;

import java.util.List;
import java.util.Map;

public class LoginActivity extends AppCompatActivity {

    private static final String TAG = "LOGIN";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        performLogin();
    }

    private void performLogin() {

        DefaultApi api = ApiProvider.getDefaultApi();
        TokenStorage tokenStorage = new TokenStorage(this);

        Log.d(TAG, "START login request");

        try {
            // ⚠️ ПРИМЕР — заменим на реальные поля позже
            String login = "test";
            String password = "test";

            api.loginPostAsync(login, password, new ApiCallback<Object>() {

                @Override
                public void onSuccess(
                        Object result,
                        int statusCode,
                        Map<String, List<String>> responseHeaders
                ) {
                    Log.d(TAG, "LOGIN SUCCESS: " + result);

                    // ❗️ПРИМЕР
                    // тут ты достанешь access / refresh из result
                    String accessToken = "ACCESS_TOKEN_FROM_RESPONSE";
                    String refreshToken = "REFRESH_TOKEN_FROM_RESPONSE";

                    tokenStorage.saveTokens(accessToken, refreshToken);
                }

                @Override
                public void onFailure(
                        ApiException e,
                        int statusCode,
                        Map<String, List<String>> responseHeaders
                ) {
                    Log.e(TAG, "LOGIN ERROR", e);
                }

                @Override
                public void onUploadProgress(long bytesWritten, long contentLength, boolean done) {}

                @Override
                public void onDownloadProgress(long bytesRead, long contentLength, boolean done) {}
            });

        } catch (ApiException e) {
            Log.e(TAG, "ApiException", e);
        }
    }
}
