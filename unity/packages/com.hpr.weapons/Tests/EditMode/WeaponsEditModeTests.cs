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

        [Test]
        public void TryFire_ConsumesAmmoAndAppliesCooldown()
        {
            var weapon = CreateWeapon();
            try
            {
                var runtime = new WeaponRuntimeState(weapon);

                Assert.That(runtime.TryFire(out WeaponFireResult result), Is.True);
                Assert.That(runtime.MagazineAmmo, Is.EqualTo(2));
                Assert.That(runtime.CooldownRemaining, Is.EqualTo(0.25f).Within(0.0001f));
                Assert.That(result.Damage, Is.EqualTo(12f));
                Assert.That(result.Pellets, Is.EqualTo(3));
                Assert.That(runtime.TryFire(out _), Is.False);

                runtime.Tick(0.25f);
                Assert.That(runtime.TryFire(out _), Is.True);
                Assert.That(runtime.MagazineAmmo, Is.EqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(weapon);
            }
        }

        [Test]
        public void Reload_TransfersOnlyNeededAmmoFromReserve()
        {
            var weapon = CreateWeapon();
            try
            {
                var runtime = new WeaponRuntimeState(weapon);
                Assert.That(runtime.TryFire(out _), Is.True);
                runtime.Tick(weapon.FireDelay);
                Assert.That(runtime.TryFire(out _), Is.True);
                runtime.Tick(weapon.FireDelay);

                Assert.That(runtime.MagazineAmmo, Is.EqualTo(1));
                Assert.That(runtime.ReserveAmmo, Is.EqualTo(5));
                Assert.That(runtime.Reload(), Is.EqualTo(2));
                Assert.That(runtime.MagazineAmmo, Is.EqualTo(3));
                Assert.That(runtime.ReserveAmmo, Is.EqualTo(3));
            }
            finally
            {
                Object.DestroyImmediate(weapon);
            }
        }

        [Test]
        public void AddReserveAmmo_RespectsMaxAmmo()
        {
            var weapon = CreateWeapon();
            weapon.MaxAmmo = 6;
            weapon.StartingReserveAmmo = 5;
            try
            {
                var runtime = new WeaponRuntimeState(weapon);
                Assert.That(runtime.AddReserveAmmo(10), Is.EqualTo(1));
                Assert.That(runtime.ReserveAmmo, Is.EqualTo(6));
            }
            finally
            {
                Object.DestroyImmediate(weapon);
            }
        }

        private static WeaponData CreateWeapon()
        {
            var weapon = ScriptableObject.CreateInstance<WeaponData>();
            weapon.Damage = 12f;
            weapon.Range = 40f;
            weapon.FireDelay = 0.25f;
            weapon.Pellets = 3;
            weapon.Spread = 0.1f;
            weapon.MagazineSize = 3;
            weapon.StartingMagazineAmmo = 3;
            weapon.StartingReserveAmmo = 5;
            weapon.MaxAmmo = 12;
            weapon.UsesAmmo = true;
            return weapon;
        }
    }
}
