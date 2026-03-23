using UnityEngine;

public enum EquipmentKind
{
    Hitscan,
    Scatter,
    Melee,
    Explosive,
    Utility
}

public enum WeaponUtilityAction
{
    None,
    ConsumeItem,
    ThreatScan,
    KeyringStatus,
    RepairTool
}

public enum ItemType
{
    Ammo,
    Consumable,
    Key,
    Utility
}

public enum EnemyAttackStyle
{
    Melee,
    Ranged
}
