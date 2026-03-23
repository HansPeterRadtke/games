using System.Text;
using UnityEngine;

public class PlayerInventory : MonoBehaviour
{
    [SerializeField] private int medkits = 1;
    [SerializeField] private int armorPatches = 1;
    [SerializeField] private bool hasRedKey;
    [SerializeField] private bool hasBlueKey;

    public int Medkits => medkits;
    public int ArmorPatches => armorPatches;
    public bool HasRedKey => hasRedKey;
    public bool HasBlueKey => hasBlueKey;

    public void ResetInventory()
    {
        medkits = 1;
        armorPatches = 1;
        hasRedKey = false;
        hasBlueKey = false;
    }

    public void ClearInventory()
    {
        medkits = 0;
        armorPatches = 0;
        hasRedKey = false;
        hasBlueKey = false;
    }

    public void AddMedkit(int amount = 1) => medkits += Mathf.Max(1, amount);
    public void AddArmorPatch(int amount = 1) => armorPatches += Mathf.Max(1, amount);
    public void AddRedKey() => hasRedKey = true;
    public void AddBlueKey() => hasBlueKey = true;

    public bool HasKey(string keyName)
    {
        return keyName switch
        {
            "Red" => hasRedKey,
            "Blue" => hasBlueKey,
            _ => true
        };
    }

    public bool UseMedkit(PlayerStats stats)
    {
        if (medkits <= 0 || stats.Health >= stats.MaxHealth - 1f)
        {
            return false;
        }

        medkits--;
        stats.Heal(35f);
        return true;
    }

    public bool UseArmorPatch(PlayerStats stats)
    {
        if (armorPatches <= 0)
        {
            return false;
        }

        armorPatches--;
        stats.Heal(10f);
        return true;
    }

    public string BuildInventorySummary(WeaponSystem weaponSystem)
    {
        var sb = new StringBuilder();
        sb.AppendLine("Equipment");
        for (int i = 0; i < weaponSystem.SlotCount; i++)
        {
            var slot = weaponSystem.GetSlot(i);
            string marker = i == weaponSystem.CurrentIndex ? ">" : " ";
            sb.AppendLine($"{marker} {i + 1}. {slot.DisplayName}  {slot.GetAmmoLabel()}");
        }
        sb.AppendLine();
        sb.AppendLine("Items");
        sb.AppendLine($"Medkits: {medkits}");
        sb.AppendLine($"Armor patches: {armorPatches}");
        sb.AppendLine($"Red key: {(hasRedKey ? "YES" : "NO")}");
        sb.AppendLine($"Blue key: {(hasBlueKey ? "YES" : "NO")}");
        sb.AppendLine();
        sb.AppendLine("Controls");
        sb.AppendLine("1-9 switch equipment");
        sb.AppendLine("LMB use current equipment");
        sb.AppendLine("R reload ranged weapons");
        return sb.ToString();
    }
}
