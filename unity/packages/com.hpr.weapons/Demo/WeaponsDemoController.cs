using System.Collections.Generic;
using UnityEngine;

public class WeaponsDemoController : MonoBehaviour
{
    [SerializeField] private List<WeaponData> weapons = new();
    [SerializeField] private List<Transform> previews = new();

    public void ValidateDemo()
    {
        if (weapons.Count < 2)
        {
            throw new System.InvalidOperationException("Weapons demo requires at least two weapon assets.");
        }

        if (previews.Count != weapons.Count)
        {
            throw new System.InvalidOperationException("Weapons demo preview count does not match weapon count.");
        }

        var ids = new HashSet<string>(System.StringComparer.Ordinal);
        for (int index = 0; index < weapons.Count; index++)
        {
            WeaponData weapon = weapons[index];
            if (weapon == null)
            {
                throw new System.InvalidOperationException($"Weapons demo weapon #{index} is missing.");
            }

            if (string.IsNullOrWhiteSpace(weapon.Id) || !ids.Add(weapon.Id))
            {
                throw new System.InvalidOperationException("Weapons demo contains a missing or duplicate weapon id.");
            }

            if (weapon.Damage <= 0f || weapon.FireDelay <= 0f)
            {
                throw new System.InvalidOperationException($"Weapon '{weapon.DisplayName}' contains invalid combat values.");
            }

            if (weapon.UsesAmmo && weapon.MaxAmmo <= 0)
            {
                throw new System.InvalidOperationException($"Weapon '{weapon.DisplayName}' is marked as ammo-based but has no ammo capacity.");
            }

            if (previews[index] == null)
            {
                throw new System.InvalidOperationException($"Weapons demo preview missing for '{weapon.DisplayName}'.");
            }
        }

        Debug.Log($"WeaponsPackageValidator: validated {weapons.Count} weapon assets.");
    }
}
