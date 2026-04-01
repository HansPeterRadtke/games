using System.Collections.Generic;
using UnityEngine;

namespace HPR
{
    public class AiDemoController : MonoBehaviour
    {
        [SerializeField] private List<EnemyData> enemies = new();
        [SerializeField] private List<Transform> previews = new();

        public void ValidateDemo()
        {
            if (enemies.Count < 2)
            {
                throw new System.InvalidOperationException("AI demo requires at least two enemy assets.");
            }

            if (previews.Count != enemies.Count)
            {
                throw new System.InvalidOperationException("AI demo preview count does not match enemy count.");
            }

            var ids = new HashSet<string>(System.StringComparer.Ordinal);
            for (int index = 0; index < enemies.Count; index++)
            {
                EnemyData enemy = enemies[index];
                if (enemy == null)
                {
                    throw new System.InvalidOperationException($"AI demo enemy #{index} is missing.");
                }

                if (string.IsNullOrWhiteSpace(enemy.Id) || !ids.Add(enemy.Id))
                {
                    throw new System.InvalidOperationException("AI demo contains a missing or duplicate enemy id.");
                }

                if (enemy.MaxHealth <= 0f || enemy.MoveSpeed <= 0f || enemy.AttackCooldown <= 0f)
                {
                    throw new System.InvalidOperationException($"Enemy '{enemy.DisplayName}' contains invalid tuning values.");
                }

                if (previews[index] == null)
                {
                    throw new System.InvalidOperationException($"AI demo preview missing for '{enemy.DisplayName}'.");
                }
            }

            Debug.Log($"AiPackageValidator: validated {enemies.Count} enemy assets.");
        }
    }
}
