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
public class ItemQuantitySaveData
{
    public string itemId;
    public int quantity;
}

[Serializable]
public class WeaponRuntimeSaveData
{
    public string weaponId;
    public int magazineAmmo;
    public int reserveAmmo;
}

[Serializable]
public class PlayerSaveData
{
    public SerializableVector3 position;
    public float yaw;
    public float pitch;
    public float health;
    public float stamina;
    public string selectedWeaponId;
    public List<WeaponRuntimeSaveData> weapons = new List<WeaponRuntimeSaveData>();
    public List<ItemQuantitySaveData> inventoryItems = new List<ItemQuantitySaveData>();
    public int skillPoints;
    public List<string> unlockedSkillIds = new List<string>();
    public List<QuestStateSaveData> questStates = new List<QuestStateSaveData>();
}

[Serializable]
public class QuestStateSaveData
{
    public string questId;
    public bool started;
    public bool completed;
    public List<int> objectiveCounts = new List<int>();
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
