using NUnit.Framework;
using UnityEngine;

namespace HPR
{
    public class WeaponsEditModeTests
    {
        [Test]
        public void WeaponData_DefaultsRemainStable()
        {
            var weapon = ScriptableObject.CreateInstance<WeaponData>();
            try
            {
                Assert.That(weapon.FireModeType, Is.EqualTo(FireModeType.Hitscan));
                Assert.That(weapon.UsesAmmo, Is.True);
                Assert.That(weapon.Pellets, Is.EqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(weapon);
            }
        }
    }
}
