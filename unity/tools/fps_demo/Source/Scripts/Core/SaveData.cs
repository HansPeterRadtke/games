using System;
using System.Collections.Generic;
using UnityEngine;

[Serializable]
public struct SerializableVector3
{
    public float x;
    public float y;
    public float z;

    public SerializableVector3(Vector3 value)
    {
        x = value.x;
        y = value.y;
        z = value.z;
    }

    public Vector3 ToVector3() => new Vector3(x, y, z);
}

[Serializable]
public struct SerializableQuaternion
{
    public float x;
    public float y;
    public float z;
    public float w;

    public SerializableQuaternion(Quaternion value)
    {
        x = value.x;
        y = value.y;
        z = value.z;
        w = value.w;
    }

    public Quaternion ToQuaternion() => new Quaternion(x, y, z, w);
}

[Serializable]
public class PlayerSaveData
{
    public SerializableVector3 position;
    public float yaw;
    public float pitch;
    public float health;
    public float stamina;
    public int currentSlot;
    public int[] magazineAmmo = new int[9];
    public int[] reserveAmmo = new int[9];
    public int medkits;
    public int armorPatches;
    public bool hasRedKey;
    public bool hasBlueKey;
}

[Serializable]
public class SaveEntityData
{
    public string id;
    public bool active = true;
    public bool boolValue;
    public int intValue;
    public float health;
    public SerializableVector3 position;
    public SerializableQuaternion rotation;
}

[Serializable]
public class SaveGameData
{
    public PlayerSaveData player = new PlayerSaveData();
    public List<SaveEntityData> entities = new List<SaveEntityData>();
}
