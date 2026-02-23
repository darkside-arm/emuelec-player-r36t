# --- PERFILES DE CONSTRUCCIÓN ---
PROFILES = {
    "r36t max": {
        "WINDOW_WIDTH": 700,
        "WINDOW_HEIGHT": 680,
        "BUTTON_B": 1,
        "BUTTON_A": 0,
        "BUTTON_X": 2,
        "BUTTON_Y": 3,
        "BUTTON_START": 9,
        "BUTTON_DUP": 14,
        "BUTTON_DDOWN": 15
    },
    "r36t": {
        "WINDOW_WIDTH": 640,
        "WINDOW_HEIGHT": 480,
        "BUTTON_B": 0,  # Ejemplo: botones invertidos
        "BUTTON_A": 1,
        "BUTTON_X": 3,
        "BUTTON_Y": 4,
        "BUTTON_START": 10,
        "BUTTON_DUP": 14,
        "BUTTON_DDOWN": 15
    },

    "r36s ultra": {
        "WINDOW_WIDTH": 700,
        "WINDOW_HEIGHT": 680,
        "BUTTON_B": 0,  # Ejemplo: botones invertidos
        "BUTTON_A": 1,
        "BUTTON_X": 3,
        "BUTTON_Y": 4,
        "BUTTON_START": 10,
        "BUTTON_DUP": 13,
        "BUTTON_DDOWN": 14
    }

}

# Selecciona el perfil activo aquí
ACTIVE_PROFILE = "r36t max"
