package com.example.smart3d2.data.storage;

import android.content.Context;
import android.content.SharedPreferences;

public class TokenStorage {

    private static final String PREFS_NAME = "auth_tokens";
    private static final String KEY_ACCESS = "access_token";
    private static final String KEY_REFRESH = "refresh_token";

    private final SharedPreferences prefs;

    public TokenStorage(Context context) {
        prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    public void saveTokens(String accessToken, String refreshToken) {
        prefs.edit()
                .putString(KEY_ACCESS, accessToken)
                .putString(KEY_REFRESH, refreshToken)
                .apply();
    }

    public String getAccessToken() {
        return prefs.getString(KEY_ACCESS, null);
    }

    public String getRefreshToken() {
        return prefs.getString(KEY_REFRESH, null);
    }

    public void clear() {
        prefs.edit().clear().apply();
    }

    public boolean hasTokens() {
        return getAccessToken() != null && getRefreshToken() != null;
    }
}
