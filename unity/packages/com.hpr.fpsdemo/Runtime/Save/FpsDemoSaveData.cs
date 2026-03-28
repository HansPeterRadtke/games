using System;
using System.Collections.Generic;

[Serializable]
public class WeaponRuntimeSaveData
{
    public string weaponId;
    public int magazineAmmo;
    public int reserveAmmo;
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
public class SaveGameData
{
    public PlayerSaveData player = new PlayerSaveData();
    public List<SaveEntityData> entities = new List<SaveEntityData>();
}
