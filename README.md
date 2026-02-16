# WiZ Bulb Sync - Ambient Light Control

This application synchronizes your computer screen's colors with your WiZ smart bulb in real-time, creating an immersive ambient lighting experience for movies, games, and videos.

### **Created by Aditya Kumar Singh**

---

## Features
-   **Real-Time Sync**: Updates your bulb 10 times per second to match on-screen action.
-   **Smart Color Match**: Uses "Dominant" color logic to ignore boring gray/black backgrounds and find the *real* color.
-   **Silky Smooth Mode**: Advanced smoothing to prevent flickering and stuttering.
-   **Vibrant Mode**: Optional toggle to boost saturation for a "neon" look.
-   **Area Selection**: Sync to a specific part of your screen (e.g., just the minimap or health bar).
-   **Brightness Control**: Master slider to dim the effect without changing your monitor brightness.

---

## Setup

### 1. Prerequisites
-   **Python 3.10+** installed on your system.
-   A **WiZ Smart Bulb** connected to the same Wi-Fi network as your PC.

### 2. Finding Your Bulb IP (New Tool!)
I have included a tool to make this easy:
1.  Double-click **`find_bulb.bat`**  or (in terminal **`.\find_bulb.bat`**)in this folder.
2.  Click **"Scan Network"**.
3.  Click on your bulb in the list to **copy its IP Address**.

### 3. Installation
1.  Double-click **`run.bat`** or (in terminal **`.\run.bat`**) to start safely.
2.  Or manually install requirements:
    ```bash
    pip install -r requirement.txt
    ```

---

## How to Run

Simply double-click **`run.bat`** or (in terminal **`.\run.bat`**) to start the application.

Or via terminal:
```bash
python main.py
```

---

## Usage Guide

1.  **Bulb IP**: Paste the IP you found earlier.
2.  **Color Logic**:
    -   **Dominant (Recommended)**: Finds the most frequent "colorful" pixel. great for games.
    -   **Average**: Mixes all colors together. Good for soft lighting.
3.  **Silky Smooth Mode**:
    -   **ON**: Colors fade gently. Best for movies.
    -   **OFF**: Instant updates. Best for competitive gaming.
4.  **Vibrant Colors**:
    -   **ON**: Boosts saturation (Red becomes *Red*).
    -   **OFF**: Accurate colors.
5.  **Select Screen Area**:
    -   Click "Select Screen Area".
    -   Drag a box over the part of the screen you want to capture.
    -   Click "Reset" to go back to full screen.

## Troubleshooting

-   **"Light isn't changing"**:
    -   Check if the **IP Address** is correct.
    -   Make sure your PC and Bulb are on the **same Wi-Fi**.
    -   Check if "Allow Local Communication" is enabled in the WiZ App settings (under Integration).

-   **"Light is stuttering / lagging"**:
    -   Turn **ON** "Silky Smooth Mode".
    -   Ensure your Wi-Fi signal is strong near the bulb.

-   **"Colors don't match"**:
    -   Try switching between **Dominant** and **Average** mode.
    -   Toggle **Vibrant Mode** on or off to see which you prefer.
