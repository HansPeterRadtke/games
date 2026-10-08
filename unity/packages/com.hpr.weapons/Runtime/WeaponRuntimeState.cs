using System;
using UnityEngine;

namespace HPR
{
    public readonly struct WeaponFireResult
    {
        public WeaponFireResult(WeaponData weapon, float damage, float range, int pellets, float spread)
        {
            Weapon = weapon;
            Damage = damage;
            Range = range;
            Pellets = pellets;
            Spread = spread;
        }

        public WeaponData Weapon { get; }
        public float Damage { get; }
        public float Range { get; }
        public int Pellets { get; }
        public float Spread { get; }
    }

    public sealed class WeaponRuntimeState
    {
        private readonly WeaponData weapon;

        public WeaponRuntimeState(WeaponData weapon)
        {
            this.weapon = weapon != null ? weapon : throw new ArgumentNullException(nameof(weapon));

            if (weapon.UsesAmmo)
            {
                MagazineAmmo = Mathf.Clamp(weapon.StartingMagazineAmmo, 0, MagazineSize);
                ReserveAmmo = weapon.MaxAmmo > 0
                    ? Mathf.Clamp(weapon.StartingReserveAmmo, 0, weapon.MaxAmmo)
                    : Mathf.Max(0, weapon.StartingReserveAmmo);
            }
        }

        public WeaponData Weapon => weapon;
        public int MagazineSize => weapon.UsesAmmo ? Mathf.Max(0, weapon.MagazineSize) : 0;
        public int MagazineAmmo { get; private set; }
        public int ReserveAmmo { get; private set; }
        public float CooldownRemaining { get; private set; }
        public bool CanFire => CooldownRemaining <= 0f && (!weapon.UsesAmmo || MagazineAmmo > 0);
        public bool CanReload => weapon.UsesAmmo && MagazineSize > 0 && MagazineAmmo < MagazineSize && ReserveAmmo > 0;

        public void Tick(float deltaTime)
        {
            if (deltaTime < 0f)
            {
                throw new ArgumentOutOfRangeException(nameof(deltaTime), "deltaTime must be non-negative.");
            }

            CooldownRemaining = Mathf.Max(0f, CooldownRemaining - deltaTime);
        }

        public bool TryFire(out WeaponFireResult result)
        {
            if (!CanFire)
            {
                result = default;
                return false;
            }

            if (weapon.UsesAmmo)
            {
                MagazineAmmo--;
            }

            CooldownRemaining = Mathf.Max(0f, weapon.FireDelay);
            result = new WeaponFireResult(
                weapon,
                weapon.Damage,
                weapon.Range,
                Mathf.Max(1, weapon.Pellets),
                Mathf.Max(0f, weapon.Spread));
            return true;
        }

        public int Reload()
        {
            if (!CanReload)
            {
                return 0;
            }

            int requested = MagazineSize - MagazineAmmo;
            int transferred = Mathf.Min(requested, ReserveAmmo);
            MagazineAmmo += transferred;
            ReserveAmmo -= transferred;
            return transferred;
        }

        public int AddReserveAmmo(int amount)
        {
            if (!weapon.UsesAmmo || amount <= 0)
            {
                return 0;
            }

            int previous = ReserveAmmo;
            if (weapon.MaxAmmo > 0)
            {
                ReserveAmmo = Mathf.Min(weapon.MaxAmmo, ReserveAmmo + amount);
            }
            else
            {
                ReserveAmmo += amount;
            }

            return ReserveAmmo - previous;
        }
    }
}
