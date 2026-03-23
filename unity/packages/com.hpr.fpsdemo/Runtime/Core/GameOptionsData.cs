using System;
using UnityEngine;

[Serializable]
public class GameOptionsData
{
    public float lookSensitivity = 2f;
    public float fieldOfView = 75f;
    public float masterVolume = 1f;
    public float musicVolume = 0.65f;
    public float sfxVolume = 0.85f;
    public bool invertY;
    public int qualityLevel;
    public KeyCode moveForward = KeyCode.W;
    public KeyCode moveBackward = KeyCode.S;
    public KeyCode moveLeft = KeyCode.A;
    public KeyCode moveRight = KeyCode.D;
    public KeyCode jump = KeyCode.Space;
    public KeyCode run = KeyCode.LeftShift;
    public KeyCode interact = KeyCode.E;
    public KeyCode inventory = KeyCode.I;
    public KeyCode map = KeyCode.M;
    public KeyCode pause = KeyCode.Escape;
    public KeyCode flashlight = KeyCode.F;
    public KeyCode reload = KeyCode.R;

    public static GameOptionsData CreateDefault()
    {
        return new GameOptionsData
        {
            qualityLevel = QualitySettings.GetQualityLevel()
        };
    }
}
