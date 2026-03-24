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

public enum FireModeType
{
    Hitscan,
    Projectile,
    Shotgun,
    Melee,
    Utility
}

public enum EnemyAIType
{
    PatrolChase,
    StationaryAttack,
    AggressiveChase
}

public enum AssetType
{
    Environment,
    Prop,
    Enemy,
    Weapon,
    Decoration
}

public enum MaterialType
{
    Unknown,
    Metal,
    Wood,
    Concrete,
    Fabric,
    Organic,
    Energy
}
